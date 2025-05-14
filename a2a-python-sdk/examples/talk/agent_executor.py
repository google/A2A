import asyncio

from collections.abc import AsyncGenerator
from typing import Any
from uuid import uuid4
from agent import TalkAgent

from typing_extensions import override

from a2a.server.agent_execution import BaseAgentExecutor
from a2a.server.events import EventQueue
from a2a.types import (
    MessageSendParams,
    Message,
    Part,
    Role,
    SendMessageRequest,
    SendStreamingMessageRequest,
    Task,
    TextPart,
)



class HelloWorldAgentExecutor(BaseAgentExecutor):
    """Test AgentProxy Implementation."""

    def __init__(self):
        self.agent = TalkAgent()

    @override
    async def on_message_send(
        self,
        request: SendMessageRequest,
        event_queue: EventQueue,
        task: Task | None,
    ) -> None:
        params: MessageSendParams = request.params
        query = self._get_user_query(params)
        result = await self.agent.invoke(query)

        message: Message = Message(
            role=Role.agent,
            parts=[Part(TextPart(text=result))],
            messageId=str(uuid4()),
        )
        print(message)
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

    def _get_user_query(self, task_send_params: MessageSendParams) -> str:
        """Helper to get user query from task send params."""
        part = task_send_params.message.parts[0].root
        if not isinstance(part, TextPart):
            raise ValueError('Only text parts are supported')
        return part.text
