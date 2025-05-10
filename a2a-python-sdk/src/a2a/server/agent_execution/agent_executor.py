from abc import ABC, abstractmethod

from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    CancelTaskRequest,
    SendMessageRequest,
    SendStreamingMessageRequest,
    Task,
    TaskResubscriptionRequest,
)


class AgentExecutor(ABC):
    """Agent Executor interface."""

    @abstractmethod
    async def on_message_send(
        self,
        request: SendMessageRequest,
        event_queue: EventQueue,
        task: Task | None,
    ) -> None:
        """Handler for 'message/send' requests."""

    @abstractmethod
    async def on_message_stream(
        self,
        request: SendStreamingMessageRequest,
        event_queue: EventQueue,
        task: Task | None,
    ) -> None:
        """Handler for 'message/stream' requests."""

    @abstractmethod
    async def on_cancel(
        self, request: CancelTaskRequest, event_queue: EventQueue, task: Task
    ) -> None:
        """Handler for 'tasks/cancel' requests."""

    @abstractmethod
    async def on_resubscribe(
        self,
        request: TaskResubscriptionRequest,
        event_queue: EventQueue,
        task: Task,
    ) -> None:
        """Handler for 'tasks/resubscribe' requests."""
