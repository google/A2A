from collections.abc import AsyncGenerator
from typing import Any

from agent import CurrencyAgent
from helpers import (
    create_task_obj,
    process_streaming_agent_response,
    update_task_with_agent_response,
)

from a2a.server import AgentExecutor, TaskStore
from a2a.types import (
    CancelTaskRequest,
    CancelTaskResponse,
    JSONRPCErrorResponse,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageStreamingRequest,
    SendMessageStreamingResponse,
    SendMessageStreamingSuccessResponse,
    SendMessageSuccessResponse,
    Task,
    TaskNotCancelableError,
    TaskResubscriptionRequest,
    TextPart,
    UnsupportedOperationError,
)


class CurrencyAgentExecutor(AgentExecutor):
    """Currency AgentExecutor Example."""

    def __init__(self, task_store: TaskStore):
        self.agent = CurrencyAgent()
        self.task_store = task_store

    async def on_message_send(
        self, request: SendMessageRequest, task: Task | None
    ) -> SendMessageResponse:
        """Handler for 'message/send' requests."""
        params: MessageSendParams = request.params
        query = self._get_user_query(params)

        if not task:
            task = create_task_obj(params)
            await self.task_store.save(task)

        # invoke the underlying agent
        agent_response: dict[str, Any] = self.agent.invoke(
            query, task.contextId
        )

        update_task_with_agent_response(task, agent_response)
        return SendMessageResponse(
            root=SendMessageSuccessResponse(id=request.id, result=task)
        )

    async def on_message_stream(  # type: ignore
        self, request: SendMessageStreamingRequest, task: Task | None
    ) -> AsyncGenerator[SendMessageStreamingResponse, None]:
        """Handler for 'message/sendStream' requests."""
        params: MessageSendParams = request.params
        query = self._get_user_query(params)

        if not task:
            task = create_task_obj(params)
            await self.task_store.save(task)

        # kickoff the streaming agent and process responses
        async for item in self.agent.stream(query, task.contextId):
            task_artifact_update_event, task_status_event = (
                process_streaming_agent_response(task, item)
            )

            if task_artifact_update_event:
                yield SendMessageStreamingResponse(
                    root=SendMessageStreamingSuccessResponse(
                        id=request.id, result=task_artifact_update_event
                    )
                )

            yield SendMessageStreamingResponse(
                root=SendMessageStreamingSuccessResponse(
                    id=request.id, result=task_status_event
                )
            )

    async def on_cancel(
        self, request: CancelTaskRequest, task: Task
    ) -> CancelTaskResponse:
        """Handler for 'tasks/cancel' requests."""
        return CancelTaskResponse(
            root=JSONRPCErrorResponse(
                id=request.id, error=TaskNotCancelableError()
            )
        )

    async def on_resubscribe(  # type: ignore
        self, request: TaskResubscriptionRequest, task: Task
    ) -> AsyncGenerator[SendMessageStreamingResponse, None]:
        """Handler for 'tasks/resubscribe' requests."""
        yield SendMessageStreamingResponse(
            root=JSONRPCErrorResponse(
                id=request.id, error=UnsupportedOperationError()
            )
        )

    def _get_user_query(self, task_send_params: MessageSendParams) -> str:
        """Helper to get user query from task send params."""
        part = task_send_params.message.parts[0].root
        if not isinstance(part, TextPart):
            raise ValueError('Only text parts are supported')
        return part.text
