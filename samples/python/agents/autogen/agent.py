from autogen import AssistantAgent, UserProxyAgent, config_list_from_json
from typing import Any, Dict, AsyncIterable, Literal, Optional, List, Tuple
from pydantic import BaseModel, Field
import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()


class ResponseFormat(BaseModel):
    """Respond to the user in this format."""
    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str


class CurrencyAgent:
    """A currency conversion agent using AutoGen."""
    
    SYSTEM_INSTRUCTION = (
        "You are a specialized assistant for currency conversions. "
        "Your sole purpose is to use the 'get_exchange_rate' tool to answer questions about currency exchange rates. "
        "If the user asks about anything other than currency conversion or exchange rates, "
        "politely state that you cannot help with that topic and can only assist with currency-related queries. "
        "Do not attempt to answer unrelated questions or use tools for other purposes."
        "Set response status to input_required if the user needs to provide more information."
        "Set response status to error if there is an error while processing the request."
        "Set response status to completed if the request is complete."
    )
    
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
    
    def __init__(self):
        self.config_list = self._get_config()
        self.assistant = self._create_assistant()
        self.user_proxy = self._create_user_proxy()
        self.tools = [self.get_exchange_rate]
        self.session_data = {}  # Store session data
    
    def _get_config(self):
        """Get API configuration for AutoGen."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        return [
            {
                "model": "gpt-4",
                "api_key": api_key,
            }
        ]
    
    def _create_assistant(self):
        """Create the assistant agent."""
        return AssistantAgent(
            name="currency_assistant",
            system_message=self.SYSTEM_INSTRUCTION,
            llm_config={"config_list": self.config_list},
        )
    
    def _create_user_proxy(self):
        """Create the user proxy agent with tools."""
        return UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            function_map={"get_exchange_rate": self.get_exchange_rate},
        )
    
    def get_exchange_rate(
        self,
        currency_from: str = "USD",
        currency_to: str = "EUR",
        currency_date: str = "latest",
    ) -> Dict[str, Any]:
        """Use this to get current exchange rate.

        Args:
            currency_from: The currency to convert from (e.g., "USD").
            currency_to: The currency to convert to (e.g., "EUR").
            currency_date: The date for the exchange rate or "latest". Defaults to "latest".

        Returns:
            A dictionary containing the exchange rate data, or an error message if the request fails.
        """    
        try:
            response = httpx.get(
                f"https://api.frankfurter.app/{currency_date}",
                params={"from": currency_from, "to": currency_to},
            )
            response.raise_for_status()

            data = response.json()
            if "rates" not in data:
                return {"error": "Invalid API response format."}
            return data
        except httpx.HTTPError as e:
            return {"error": f"API request failed: {e}"}
        except ValueError:
            return {"error": "Invalid JSON response from API."}
    
    def _format_response(self, response: str) -> Dict[str, Any]:
        """Format the agent's response for the API."""
        try:
            # Try to extract the ResponseFormat from the response
            response_lines = response.strip().split('\n')
            
            # Find JSON-like content
            json_content = None
            for i, line in enumerate(response_lines):
                if '{"status":' in line or '"status":' in line:
                    try:
                        # Extract the JSON part
                        json_start = line.find('{')
                        json_end = line.rfind('}') + 1
                        if json_start >= 0 and json_end > json_start:
                            json_content = line[json_start:json_end]
                            parsed = json.loads(json_content)
                            if "status" in parsed and "message" in parsed:
                                status = parsed["status"]
                                message = parsed["message"]
                                
                                is_task_complete = status == "completed"
                                require_user_input = status == "input_required"
                                
                                return {
                                    "is_task_complete": is_task_complete,
                                    "require_user_input": require_user_input,
                                    "content": message
                                }
                    except json.JSONDecodeError:
                        continue
            
            # If we couldn't extract structured data, provide a default response
            if "i need more information" in response.lower():
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": response
                }
            else:
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": response
                }
                
        except Exception as e:
            # Default response in case of parsing errors
            return {
                "is_task_complete": False,
                "require_user_input": True,
                "content": f"Error processing response: {str(e)}\n\nOriginal response: {response}"
            }
    
    def invoke(self, query: str, sessionId: str) -> Dict[str, Any]:
        """Process a query synchronously.
        
        Args:
            query: The user's query text
            sessionId: A unique session identifier
            
        Returns:
            Formatted response with task completion status and content
        """
        # Save context per session
        if sessionId not in self.session_data:
            self.session_data[sessionId] = []
        
        # Reset conversation for this session
        self.assistant.reset()
        self.user_proxy.reset()
        
        # Start the conversation with the query
        self.user_proxy.initiate_chat(
            self.assistant, 
            message=query,
            clear_history=False
        )
        
        # Get the last assistant message
        chat_history = self.assistant.chat_messages[self.user_proxy.name]
        response = chat_history[-1]["content"] if chat_history else "I couldn't process your request."
        
        # Store chat history for the session
        self.session_data[sessionId].append({"role": "user", "content": query})
        self.session_data[sessionId].append({"role": "assistant", "content": response})
        
        return self._format_response(response)
    
    async def stream(self, query: str, sessionId: str) -> AsyncIterable[Dict[str, Any]]:
        """Process a query with streaming responses.
        
        Args:
            query: The user's query text
            sessionId: A unique session identifier
            
        Yields:
            Formatted response chunks with status updates
        """
        # Save context per session
        if sessionId not in self.session_data:
            self.session_data[sessionId] = []
        
        # Add the user query to session data
        self.session_data[sessionId].append({"role": "user", "content": query})
        
        # Reset conversation for this session
        self.assistant.reset()
        self.user_proxy.reset()
        
        # First, yield a "thinking" status
        yield {
            "is_task_complete": False,
            "require_user_input": False,
            "content": "Looking up the exchange rates..."
        }
        
        # Process the query
        self.user_proxy.initiate_chat(
            self.assistant, 
            message=query,
            clear_history=False
        )
        
        # After processing, yield the "processing" status
        yield {
            "is_task_complete": False,
            "require_user_input": False,
            "content": "Processing the exchange rates.."
        }
        
        # Get the final response
        chat_history = self.assistant.chat_messages[self.user_proxy.name]
        response = chat_history[-1]["content"] if chat_history else "I couldn't process your request."
        
        # Store the assistant response in session data
        self.session_data[sessionId].append({"role": "assistant", "content": response})
        
        # Yield the final formatted response
        yield self._format_response(response)
