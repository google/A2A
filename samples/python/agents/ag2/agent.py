import logging
import os
import traceback
import json
from dotenv import load_dotenv
from typing import AsyncIterable, Any, Literal
from pydantic import BaseModel

from autogen import AssistantAgent, LLMConfig
from autogen.mcp import create_toolkit

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

class ResponseModel(BaseModel):
    """Response model for the YouTube MCP agent."""
    text_reply: str
    closed_captions: str | None
    status: Literal["TERMINATE", ""]
    
    def format(self) -> str:
        """Format the response as a string."""
        if self.closed_captions is None:
            return self.text_reply
        else:
            return f"{self.text_reply}\n\nClosed Captions:\n{self.closed_captions}"


def get_api_key() -> str:
    """Helper method to handle API Key."""
    load_dotenv()
    return os.getenv("OPENAI_API_KEY")

class YoutubeMCPAgent:
    """Agent to access a Youtube MCP Server to download closed captions"""

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        # Import AG2 dependencies here to isolate requirements
        try:
            # Set up LLM configuration with response format
            llm_config = LLMConfig(
                model="gpt-4o",
                api_key=get_api_key(),
                response_format=ResponseModel
            )

            # Create the assistant agent that will use MCP tools
            self.agent = AssistantAgent(
                name="YoutubeMCPAgent",
                llm_config=llm_config,
                system_message=(
                    "You are a specialized assistant for processing YouTube videos. "
                    "You can use MCP tools to fetch captions and process YouTube content. "
                    "You can provide captions, summarize videos, or analyze content from YouTube. "
                    "If the user asks about anything not related to YouTube videos or doesn't provide a YouTube URL, "
                    "politely state that you can only help with tasks related to YouTube videos.\n\n"
                    "IMPORTANT: Always respond using the ResponseModel format with these fields:\n"
                    "- text_reply: Your main response text\n"
                    "- closed_captions: YouTube captions if available, null if not relevant\n"
                    "- status: Always use 'TERMINATE' for all responses \n\n"
                    "Example response:\n"
                    "{\n"
                    "  \"text_reply\": \"Here's the information you requested...\",\n"
                    "  \"closed_captions\": null,\n"
                    "  \"status\": \"TERMINATE\"\n"
                    "}"
                ),
            )

            self.initialized = True
            logger.info("MCP Agent initialized successfully")
        except ImportError as e:
            logger.error(f"Failed to import AG2 components: {e}")
            self.initialized = False

    def get_agent_response(self, response: str) -> dict[str, Any]:
        """Format agent response in a consistent structure."""
        try:
            # Try to parse the response as a ResponseModel JSON
            response_dict = json.loads(response)
            model = ResponseModel(**response_dict)
            
            # All final responses should be treated as complete
            return {
                "is_task_complete": True,
                "require_user_input": False,
                "content": model.format()
            }
        except Exception as e:
            # Log but continue with best-effort fallback
            logger.error(f"Error parsing response: {e}, response: {response}")
            
            # Default to treating it as a completed response
            return {
                "is_task_complete": True, 
                "require_user_input": False,
                "content": response
            }

    async def stream(self, query: str, sessionId: str) -> AsyncIterable[dict[str, Any]]:
        """Stream updates from the MCP agent."""
        if not self.initialized:
            yield {
                "is_task_complete": False,
                "require_user_input": True,
                "content": "Agent initialization failed. Please check the dependencies and logs."
            }
            return

        try:
            # Initial response to acknowledge the query
            yield {
                "is_task_complete": False,
                "require_user_input": False,
                "content": "Processing request..."
            }

            logger.info(f"Processing query: {query[:50]}...")

            try:                
                # Create stdio server parameters for mcp-youtube
                server_params = StdioServerParameters(
                    command="mcp-youtube",
                )

                # Connect to the MCP server using stdio client
                async with stdio_client(server_params) as (read, write), ClientSession(read, write) as session:
                    # Initialize the connection
                    await session.initialize()

                    # Create toolkit and register tools
                    toolkit = await create_toolkit(session=session)
                    toolkit.register_for_llm(self.agent)

                    result = await self.agent.a_run(
                        message=query,
                        tools=toolkit.tools,
                        max_turns=2,  # Fixed at 2 turns to allow tool usage
                        user_input=False,
                    )

                    # Extract the content from the result
                    try:
                        # Process the result
                        await result.process()
                        
                        # Get the summary which contains the output
                        response = await result.summary

                    except Exception as extraction_error:
                        logger.error(f"Error extracting response: {extraction_error}")
                        traceback.print_exc()
                        response = f"Error processing request: {str(extraction_error)}"

                    # Final response
                    yield self.get_agent_response(response)
                    
            except Exception as e:
                logger.error(f"Error during processing: {traceback.format_exc()}")
                yield {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": f"Error processing request: {str(e)}"
                }
        except Exception as e:
            logger.error(f"Error in streaming agent: {traceback.format_exc()}")
            yield {
                "is_task_complete": False,
                "require_user_input": True,
                "content": f"Error processing request: {str(e)}"
            }

    def invoke(self, query: str, sessionId: str) -> dict[str, Any]:
        """Synchronous invocation of the MCP agent."""
        raise NotImplementedError(
            "Synchronous invocation is not supported by this agent. Use the streaming endpoint (tasks/sendSubscribe) instead."
        )
