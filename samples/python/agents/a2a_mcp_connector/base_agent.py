"""
Base class for agents that implement the A2A TaskManager interface.
This is in a separate file to avoid circular imports.
"""

import asyncio
import json
import logging
from typing import Any, AsyncIterable, Dict, List, Optional, Tuple
import os
import sys

# Add the parent directory to the Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from common.types import Message, Part, TextPart, DataPart, TaskState, TaskStatus
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentWithTaskManager:
    """Base class for agents that need to implement the A2A TaskManager interface."""

    def get_processing_message(self) -> str:
        """Get a message to show while the task is being processed."""
        return "Processing..."

    async def process_message(
        self, message: Message, task_id: str, streaming: bool = False
    ) -> AsyncIterable[Tuple[TaskState, Optional[Message], Optional[str]]]:
        """
        Process a message from the user.
        
        Args:
            message: The message to process
            task_id: The ID of the task
            streaming: Whether to stream the response
            
        Yields:
            Tuples of (task_state, response_message, metadata_json)
        """
        try:
            logger.info(f"Processing message for task {task_id}")
            session_id = message.metadata.get("session_id", "default-session")
            
            # If the message has parts but they're not what we expect, yield an error
            if not message.parts or not any(
                isinstance(p, TextPart) or isinstance(p, DataPart) for p in message.parts
            ):
                error_message = Message(
                    role="agent",
                    parts=[TextPart(text="I can only process text or data messages.")],
                    metadata={"task_id": task_id, "session_id": session_id},
                )
                yield (TaskState.FAILED, error_message, None)
                return

            # Convert the message to an ADK content object
            message_content = self.message_to_adk_content(message)
            
            # Create a thinking message to show while processing
            thinking_message = Message(
                role="agent",
                parts=[TextPart(text=self.get_processing_message())],
                metadata={"task_id": task_id, "session_id": session_id, "is_thinking": True},
            )
            
            # Yield the thinking message and set the task state to working
            yield (TaskState.WORKING, thinking_message, None)

            # Generate the agent response using ADK Runner
            try:
                runner = self._runner
                # Create a new conversation or continue an existing one based on session ID
                chat = await runner.start_chat(
                    session_id=session_id
                )
                response = await chat.send_message(
                    content=message_content
                )
                
                response_message = self.adk_content_to_message(response.content, task_id, session_id)
                
                yield (TaskState.COMPLETED, response_message, None)
                
            except Exception as e:
                logger.error(f"Error generating response: {e}")
                error_message = Message(
                    role="agent",
                    parts=[TextPart(text=f"Error processing your request: {e}")],
                    metadata={"task_id": task_id, "session_id": session_id},
                )
                yield (TaskState.FAILED, error_message, None)
                
        except Exception as e:
            logger.error(f"Error in process_message: {e}")
            error_message = Message(
                role="agent",
                parts=[TextPart(text=f"An unexpected error occurred: {e}")],
                metadata={"task_id": task_id},
            )
            yield (TaskState.FAILED, error_message, None)

    def message_to_adk_content(self, message: Message) -> types.Content:
        """Convert an A2A message to an ADK content object."""
        parts = []
        
        for part in message.parts:
            if isinstance(part, TextPart):
                adk_part = types.Part()
                adk_part.text = part.text
                parts.append(adk_part)
            elif isinstance(part, DataPart):
                adk_part = types.Part()
                adk_part.text = json.dumps(part.data)
                parts.append(adk_part)
        
        return types.Content(
            parts=parts,
            role=message.role,
        )

    def adk_content_to_message(self, content: types.Content, task_id: str, session_id: str) -> Message:
        """Convert an ADK content object to an A2A message."""
        parts = []
        
        for part in content.parts:
            if hasattr(part, "text") and part.text:
                # Try to parse as JSON first
                try:
                    data = json.loads(part.text)
                    parts.append(DataPart(data=data))
                except json.JSONDecodeError:
                    # If it's not JSON, treat it as plain text
                    parts.append(TextPart(text=part.text))
            elif hasattr(part, "functionCall"):
                function_call_data = {
                    "function_call": {
                        "name": part.functionCall.name,
                        "args": json.loads(part.functionCall.args) if part.functionCall.args else {},
                    }
                }
                parts.append(DataPart(data=function_call_data))
        
        return Message(
            role=content.role,
            parts=parts,
            metadata={"task_id": task_id, "session_id": session_id},
        )