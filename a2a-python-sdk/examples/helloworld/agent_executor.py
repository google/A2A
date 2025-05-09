import asyncio

from collections.abc import AsyncGenerator
from typing import Any
from uuid import uuid4

from a2a.server import AgentExecutor
from a2a.types import (
    CancelTaskRequest,
    CancelTaskResponse,
    JSONRPCErrorResponse,
    Message,
    Part,
    Role,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageStreamingRequest,
    SendMessageStreamingResponse,
    SendMessageStreamingSuccessResponse,
    SendMessageSuccessResponse,
    Task,
    TaskResubscriptionRequest,
    TextPart,
    UnsupportedOperationError,
)


class HelloWorldAgent:
    """Hello World Agent."""

    async def invoke(self):
        return 'Hello World'

    async def stream(self) -> AsyncGenerator[dict[str, Any], None]:
        yield {'content': 'Hello ', 'done': False}
        await asyncio.sleep(2)
        yield {'content': 'World', 'done': True}


class HelloWorldAgentExecutor(AgentExecutor):
    """Test AgentProxy Implementation."""

    def __init__(self):
        self.agent = HelloWorldAgent()

    async def on_message_send(
        self, request: SendMessageRequest, task: Task | None
    ) -> SendMessageResponse:
        result = await self.agent.invoke()

        message: Message = Message(
            role=Role.agent,
            parts=[Part(root=TextPart(text=result))],
            messageId=str(uuid4()),
        )

        return SendMessageResponse(
            root=SendMessageSuccessResponse(id=request.id, result=message)
        )

    async def on_message_stream(  # type: ignore
        self, request: SendMessageStreamingRequest, task: Task | None
    ) -> AsyncGenerator[SendMessageStreamingResponse, None]:
        async for chunk in self.agent.stream():
            message: Message = Message(
                role=Role.agent,
                parts=[Part(root=TextPart(text=chunk['content']))],
                messageId=str(uuid4()),
                final=chunk['done'],
            )
            yield SendMessageStreamingResponse(
                root=SendMessageStreamingSuccessResponse(
                    id=request.id, result=message
                )
            )

    async def on_cancel(
        self, request: CancelTaskRequest, task: Task
    ) -> CancelTaskResponse:
        return CancelTaskResponse(
            root=JSONRPCErrorResponse(
                id=request.id, error=UnsupportedOperationError()
            )
        )

    async def on_resubscribe(  # type: ignore
        self, request: TaskResubscriptionRequest, task: Task
    ) -> AsyncGenerator[SendMessageStreamingResponse, None]:
        yield SendMessageStreamingResponse(
            root=JSONRPCErrorResponse(
                id=request.id, error=UnsupportedOperationError()
            )
        )
