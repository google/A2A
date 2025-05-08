from typing import AsyncIterable, Dict, Any, Literal, Union, cast
from pydantic import BaseModel
import anthropic
from anthropic.types import MessageParam, TextBlock, ToolUnionParam, ToolUseBlock
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
from dataclasses import dataclass, field
import os
import logging
from dotenv import load_dotenv
load_dotenv()

# Initialize Anthropic client
anthropic_client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

logger = logging.getLogger(__name__)

class ResponseFormat(BaseModel):
    """Respond to the user in this format."""
    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str

@dataclass
class Chat:
    messages: list[MessageParam] = field(default_factory=list)
    system_prompt: str = """You are a master SQL assistant. 
    Your job is to use the tools at your disposal to execute SQL queries and provide the results to the user.
    Set response status to input_required if the user needs to provide more information.
    Set response status to error if there is an error while processing the request.
    Set response status to completed if the request is complete."""

    async def process_query(self, session: ClientSession, query: str) -> AsyncIterable[Dict[str, Any]]:
        try:
            response = await session.list_tools()
            available_tools: list[ToolUnionParam] = [
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "input_schema": tool.inputSchema,
                }
                for tool in response.tools
            ]

            # Initial Claude API call
            res = await anthropic_client.messages.create(
                model="claude-3-5-sonnet-latest",
                system=self.system_prompt,
                max_tokens=8000,
                messages=self.messages,
                tools=available_tools,
            )

            assistant_message_content: list[Union[ToolUseBlock, TextBlock]] = []
            for content in res.content:
                try:
                    if content.type == "text":
                        assistant_message_content.append(content)
                        yield {
                            "is_task_complete": False,
                            "require_user_input": False,
                            "content": content.text
                        }
                    elif content.type == "tool_use":
                        tool_name = content.name
                        tool_args = content.input

                        # Execute tool call
                        result = await session.call_tool(tool_name, cast(dict, tool_args))

                        assistant_message_content.append(content)
                        self.messages.append(
                            {"role": "assistant", "content": assistant_message_content}
                        )
                        self.messages.append(
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": content.id,
                                        "content": getattr(result.content[0], "text", ""),
                                    }
                                ],
                            }
                        )
                        # Get next response from Claude
                        res = await anthropic_client.messages.create(
                            model="claude-3-5-sonnet-latest",
                            max_tokens=8000,
                            messages=self.messages,
                            tools=available_tools,
                        )
                        self.messages.append(
                            {
                                "role": "assistant",
                                "content": getattr(res.content[0], "text", ""),
                            }
                        )
                        yield {
                            "is_task_complete": True,
                            "require_user_input": False,
                            "content": getattr(res.content[0], "text", "")
                        }
                except Exception as e:
                    logger.error(f"Error processing content: {e}")
                    yield {
                        "is_task_complete": True,
                        "require_user_input": False,
                        "content": f"An error occurred while processing the response: {str(e)}"
                    }
        except Exception as e:
            logger.error(f"Error in process_query: {e}")
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": f"An error occurred: {str(e)}"
            }

class MCPAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self.chat = Chat()
        self.server_params = StdioServerParameters(
            command="python",
            args=["./mcp_server.py"],
            env=None,
        )

    async def stream(self, query: str, sessionId: str) -> AsyncIterable[Dict[str, Any]]:
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                self.chat.messages.append(
                    MessageParam(
                        role="user",
                        content=query,
                    )
                )
                async for response in self.chat.process_query(session, query):
                    yield response

    def invoke(self, query: str, sessionId: str) -> Dict[str, Any]:
        # For non-streaming requests, we'll run the streaming version in an event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            responses = []
            async def collect_responses():
                async with stdio_client(self.server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        self.chat.messages.append(
                            MessageParam(
                                role="user",
                                content=query,
                            )
                        )
                        async for response in self.chat.process_query(session, query):
                            responses.append(response)
            
            loop.run_until_complete(collect_responses())
            # Return the last response
            return responses[-1] if responses else {
                "is_task_complete": True,
                "require_user_input": False,
                "content": "No response generated."
            }
        finally:
            loop.close() 