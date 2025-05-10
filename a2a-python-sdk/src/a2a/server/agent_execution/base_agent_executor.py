from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    A2AError,
    CancelTaskRequest,
    SendMessageRequest,
    SendStreamingMessageRequest,
    Task,
    TaskResubscriptionRequest,
    UnsupportedOperationError,
)


class BaseAgentExecutor(AgentExecutor):
    """Base AgentExecutor which returns unsupported operation error."""

    async def on_message_send(
        self,
        request: SendMessageRequest,
        event_queue: EventQueue,
        task: Task | None,
    ) -> None:
        """Handler for 'message/send' requests."""
        event_queue.enqueue_event(A2AError(UnsupportedOperationError()))

    async def on_message_stream(
        self,
        request: SendStreamingMessageRequest,
        event_queue: EventQueue,
        task: Task | None,
    ) -> None:
        """Handler for 'message/stream' requests."""
        event_queue.enqueue_event(A2AError(UnsupportedOperationError()))

    async def on_cancel(
        self, request: CancelTaskRequest, event_queue: EventQueue, task: Task
    ) -> None:
        """Handler for 'tasks/cancel' requests."""
        event_queue.enqueue_event(A2AError(UnsupportedOperationError()))

    async def on_resubscribe(
        self,
        request: TaskResubscriptionRequest,
        event_queue: EventQueue,
        task: Task,
    ) -> None:
        """Handler for 'tasks/resubscribe' requests."""
        event_queue.enqueue_event(A2AError(UnsupportedOperationError()))
