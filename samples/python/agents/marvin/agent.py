import logging
import os
import threading
from collections.abc import AsyncIterable
from typing import Annotated, Any, ClassVar

from common.types import TextPart
from pydantic import BaseModel, Field

import marvin

logger = logging.getLogger(__name__)


ClarifyingQuestion = Annotated[
    str, Field(description="A clarifying question to ask the user")
]


def _to_text_part(text: str) -> TextPart:
    return TextPart(type="text", text=text)


class ExtractionOutcome[T](BaseModel):
    """Represents the result of trying to extract contact info."""

    extracted_data: T
    summary: str = Field(
        description="summary of the extracted information.",
    )


class ExtractorAgent[T]:
    """Contact information extraction agent using Marvin framework."""

    SUPPORTED_CONTENT_TYPES: ClassVar[list[str]] = [
        "text",
        "text/plain",
        "application/json",
    ]

    def __init__(self, instructions: str, result_type: type[T]):
        self.instructions = instructions
        self.result_type = result_type

    async def invoke(self, query: str, sessionId: str) -> dict[str, Any]:
        """Process a user query with marvin

        Args:
            query: The user's input text.
            sessionId: The session identifier

        Returns:
            A dictionary describing the outcome and necessary next steps.
        """
        try:
            logger.debug(
                f"[Session: {sessionId}] PID: {os.getpid()} | PyThread: {threading.get_ident()} | Using/Creating MarvinThread ID: {sessionId}"
            )

            result = await marvin.run_async(
                query,
                context={
                    "your personality": self.instructions,
                    "reminder": "Use your memory to help fill out the form",
                },
                thread=marvin.Thread(id=sessionId),
                result_type=ExtractionOutcome[self.result_type] | ClarifyingQuestion,
            )

            if isinstance(result, ExtractionOutcome):
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "text_parts": [_to_text_part(result.summary)],
                    "data": result.extracted_data.model_dump(),
                }
            else:
                assert isinstance(result, str)
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "text_parts": [_to_text_part(result)],
                    "data": None,
                }

        except Exception as e:
            logger.exception(f"Error during agent invocation for session {sessionId}")
            return {
                "is_task_complete": False,
                "require_user_input": True,
                "text_parts": [
                    _to_text_part(
                        f"Sorry, I encountered an error processing your request: {str(e)}"
                    )
                ],
                "data": None,
            }

    async def stream(self, query: str, sessionId: str) -> AsyncIterable[dict[str, Any]]:
        """Stream the response for a user query.

        Args:
            query: The user's input text.
            sessionId: The session identifier.

        Returns:
            An asynchronous iterable of response dictionaries.
        """
        yield {
            "is_task_complete": False,
            "require_user_input": False,
            "content": "Analyzing your text for contact information...",
        }

        yield await self.invoke(query, sessionId)
