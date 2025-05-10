import asyncio

from collections.abc import AsyncGenerator
from typing import Any
from uuid import uuid4

from typing_extensions import override

from a2a.server.agent_execution import BaseAgentExecutor
from a2a.server.events import EventQueue
from a2a.types import (
    Message,
    Part,
    Role,
    SendMessageRequest,
    SendStreamingMessageRequest,
    Task,
    TextPart,
)


class HelloWorldAgent:
    """Hello World Agent."""

    async def invoke(self):
        return 'Hello World'

    async def stream(self) -> AsyncGenerator[dict[str, Any], None]:
        yield {'content': 'Hello ', 'done': False}
        await asyncio.sleep(2)
        yield {'content': 'World', 'done': True}


class HelloWorldAgentExecutor(BaseAgentExecutor):
    """Test AgentProxy Implementation."""

    def __init__(self):
        self.agent = HelloWorldAgent()

    @override
    async def on_message_send(
        self,
        request: SendMessageRequest,
        event_queue: EventQueue,
        task: Task | None,
    ) -> None:
        result = await self.agent.invoke()

        message: Message = Message(
            role=Role.agent,
            parts=[Part(TextPart(text=result))],
            messageId=str(uuid4()),
        )
        event_queue.enqueue_event(message)

    @override
    async def on_message_stream(
        self,
        request: SendStreamingMessageRequest,
        event_queue: EventQueue,
        task: Task | None,
    ) -> None:
        async for chunk in self.agent.stream():
            message: Message = Message(
                role=Role.agent,
                parts=[Part(TextPart(text=chunk['content']))],
                messageId=str(uuid4()),
                final=chunk['done'],
            )
            event_queue.enqueue_event(message)
