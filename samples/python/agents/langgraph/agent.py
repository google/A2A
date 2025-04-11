import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from langchain_cohere import ChatCohere
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_fireworks import ChatFireworks
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_together import ChatTogether
from databricks_langchain import ChatDatabricks
from langchain_ibm import ChatWatsonx
from langchain_xai import ChatXAI
from langchain_perplexity import ChatPerplexity
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, ToolMessage
import httpx
from typing import Any, Dict, AsyncIterable, Literal
from pydantic import BaseModel

memory = MemorySaver()


SUPPORTED_API_KEYS = {
    "GOOGLE_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "GROQ_API_KEY",
    "COHERE_API_KEY",
    "NVIDIA_API_KEY",
    "FIREWORKS_API_KEY",
    "MISTRAL_API_KEY",
    "TOGETHER_API_KEY",
    "WATSONX_API_KEY",
    "DATABRICKS_API_KEY",
    "XAI_API_KEY",
    "PPLX_API_KEY",
}


def get_api_key() -> str:
    """Helper method to handle API Key."""
    return next(
        (os.getenv(var) for var in SUPPORTED_API_KEYS if os.getenv(var) is not None),
        None,
    )


@tool
def get_exchange_rate(
    currency_from: str = "USD",
    currency_to: str = "EUR",
    currency_date: str = "latest",
):
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


class ResponseFormat(BaseModel):
    """Respond to the user in this format."""
    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str

class CurrencyAgent:

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

    def __init__(self):
        match get_api_key():
            case "GOOGLE_API_KEY":
                model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
            case "OPENAI_API_KEY":
                model = ChatOpenAI(model="gpt-4o-mini")
            case "ANTHROPIC_API_KEY":
                model = ChatAnthropic(model="claude-3-5-sonnet-latest")
            case "AZURE_OPENAI_API_KEY":
                if (
                    os.getenv("AZURE_OPENAI_ENDPOINT")
                    and os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
                    and os.getenv("AZURE_OPENAI_API_VERSION")
                ):
                    model = AzureChatOpenAI(
                        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                    )
                else:
                    raise ValueError(
                        "AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME, and AZURE_OPENAI_API_VERSION not set."
                    )
            case "GROQ_API_KEY":
                model = ChatGroq(temperature=0, model_name="llama3-8b-8192")
            case "COHERE_API_KEY":
                model = ChatCohere("command-r-plus")
            case "NVIDIA_API_KEY":
                model = ChatNVIDIA(model="meta/llama3-70b-instruct")
            case "FIREWORKS_API_KEY":
                model = ChatFireworks(model="accounts/fireworks/models/llama-v3p1-70b-instruct")
            case "MISTRAL_API_KEY":
                model = ChatMistralAI(model="mistral-large-latest")
            case "TOGETHER_API_KEY":
                model = ChatTogether(model="mistralai/Mixtral-8x7B-Instruct-v0.1")
            case "WATSONX_API_KEY":
                model = ChatWatsonx(model="ibm/granite-34b-code-instruct")
            case "DATABRICKS_API_KEY":
                if os.getenv("DATABRICKS_HOST"):
                    model = ChatDatabricks(endpoint="databricks-meta-llama-3-1-70b-instruct")
                else:
                    raise ValueError("DATABRICKS_HOST not found in environment variables.")
            case "XAI_API_KEY":
                model = ChatXAI(model="grok-2")
            case "PPLX_API_KEY":
                model = ChatPerplexity(model="llama-3.1-sonar-small-128k-online")
            case _:
                raise ValueError("No valid API key found in environment variables.")
        self.model = model
        self.tools = [get_exchange_rate]

        self.graph = create_react_agent(
            self.model, tools=self.tools, checkpointer=memory, prompt = self.SYSTEM_INSTRUCTION, response_format=ResponseFormat
        )

    def invoke(self, query, sessionId) -> str:
        config = {"configurable": {"thread_id": sessionId}}
        self.graph.invoke({"messages": [("user", query)]}, config)        
        return self.get_agent_response(config)

    async def stream(self, query, sessionId) -> AsyncIterable[Dict[str, Any]]:
        inputs = {"messages": [("user", query)]}
        config = {"configurable": {"thread_id": sessionId}}

        for item in self.graph.stream(inputs, config, stream_mode="values"):
            message = item["messages"][-1]
            if (
                isinstance(message, AIMessage)
                and message.tool_calls
                and len(message.tool_calls) > 0
            ):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "Looking up the exchange rates...",
                }
            elif isinstance(message, ToolMessage):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "Processing the exchange rates..",
                }            
        
        yield self.get_agent_response(config)

        
    def get_agent_response(self, config):
        current_state = self.graph.get_state(config)        
        structured_response = current_state.values.get('structured_response')
        if structured_response and isinstance(structured_response, ResponseFormat): 
            if structured_response.status == "input_required":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured_response.message
                }
            elif structured_response.status == "error":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured_response.message
                }
            elif structured_response.status == "completed":
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": structured_response.message
                }

        return {
            "is_task_complete": False,
            "require_user_input": True,
            "content": "We are unable to process your request at the moment. Please try again.",
        }

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
