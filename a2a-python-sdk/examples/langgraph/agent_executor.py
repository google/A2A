from typing import Any

from agent import CurrencyAgent
from helpers import (
    process_streaming_agent_response,
    update_task_with_agent_response,
)
from typing_extensions import override

from a2a.server.agent_execution import BaseAgentExecutor
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
    Task,
    TextPart,
)
from a2a.utils import create_task_obj


class CurrencyAgentExecutor(BaseAgentExecutor):
    """Currency AgentExecutor Example."""

    def __init__(self):
        self.agent = CurrencyAgent()

    @override
    async def on_message_send(
        self,
        request: SendMessageRequest,
        event_queue: EventQueue,
        task: Task | None,
    ) -> None:
        """Handler for 'message/send' requests."""
        params: MessageSendParams = request.params
        query = self._get_user_query(params)

        if not task:
            task = create_task_obj(params)

        # invoke the underlying agent
        agent_response: dict[str, Any] = self.agent.invoke(
            query, task.contextId
        )
        update_task_with_agent_response(task, agent_response)
        event_queue.enqueue_event(task)

    @override
    async def on_message_stream(
        self,
        request: SendStreamingMessageRequest,
        event_queue: EventQueue,
        task: Task | None,
    ) -> None:
        """Handler for 'message/stream' requests."""
        params: MessageSendParams = request.params
        query = self._get_user_query(params)

        if not task:
            task = create_task_obj(params)
            # emit the initial task so it is persisted to TaskStore
            event_queue.enqueue_event(task)

        # kickoff the streaming agent and process responses
        async for item in self.agent.stream(query, task.contextId):
            task_artifact_update_event, task_status_event = (
                process_streaming_agent_response(task, item)
            )

            if task_artifact_update_event:
                event_queue.enqueue_event(task_artifact_update_event)

            event_queue.enqueue_event(task_status_event)

    def _get_user_query(self, task_send_params: MessageSendParams) -> str:
        """Helper to get user query from task send params."""
        part = task_send_params.message.parts[0].root
        if not isinstance(part, TextPart):
            raise ValueError('Only text parts are supported')
        return part.text
