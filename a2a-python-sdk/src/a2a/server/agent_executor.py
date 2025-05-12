from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from a2a.types import (
    CancelTaskRequest,
    CancelTaskResponse,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageStreamingRequest,
    SendMessageStreamingResponse,
    Task,
    TaskResubscriptionRequest,
)


class AgentExecutor(ABC):
    """Agent Executor interface."""

    @abstractmethod
    async def on_message_send(
        self, request: SendMessageRequest, task: Task | None
    ) -> SendMessageResponse:
        pass

    @abstractmethod
    async def on_message_stream(
        self, request: SendMessageStreamingRequest, task: Task | None
    ) -> AsyncGenerator[SendMessageStreamingResponse, None]:
        pass

    @abstractmethod
    async def on_cancel(
        self, request: CancelTaskRequest, task: Task
    ) -> CancelTaskResponse:
        pass

    @abstractmethod
    async def on_resubscribe(
        self, request: TaskResubscriptionRequest, task: Task
    ) -> AsyncGenerator[SendMessageStreamingResponse, None]:
        pass
