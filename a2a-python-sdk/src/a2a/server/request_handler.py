import asyncio
import logging

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from a2a.server.agent_executor import AgentExecutor
from a2a.server.streaming_response_queue import StreamingResponseQueue
from a2a.server.task_store import InMemoryTaskStore, TaskStore
from a2a.types import (
    A2AError,
    CancelTaskRequest,
    CancelTaskResponse,
    CancelTaskSuccessResponse,
    GetTaskPushNotificationConfigRequest,
    GetTaskPushNotificationConfigResponse,
    GetTaskRequest,
    GetTaskResponse,
    GetTaskSuccessResponse,
    InternalError,
    JSONRPCError,
    JSONRPCErrorResponse,
    Message,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageStreamingRequest,
    SendMessageStreamingResponse,
    SendMessageStreamingSuccessResponse,
    SendMessageSuccessResponse,
    SetTaskPushNotificationConfigRequest,
    SetTaskPushNotificationConfigResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskIdParams,
    TaskNotFoundError,
    TaskQueryParams,
    TaskResubscriptionRequest,
    TaskStatusUpdateEvent,
    UnsupportedOperationError,
)
from a2a.utils import append_artifact_to_task


logger = logging.getLogger(__name__)


class A2ARequestHandler(ABC):
    """A2A request handler interface."""

    @abstractmethod
    async def on_get_task(self, request: GetTaskRequest) -> GetTaskResponse:
        pass

    @abstractmethod
    async def on_cancel_task(
        self, request: CancelTaskRequest
    ) -> CancelTaskResponse:
        pass

    @abstractmethod
    async def on_message_send(
        self, request: SendMessageRequest
    ) -> SendMessageResponse:
        pass

    @abstractmethod
    async def on_message_send_stream(
        self, request: SendMessageStreamingRequest
    ) -> AsyncGenerator[SendMessageStreamingResponse, None]:
        yield SendMessageStreamingResponse(
            root=JSONRPCErrorResponse(
                id=request.id, error=UnsupportedOperationError()
            )
        )

    @abstractmethod
    async def on_set_task_push_notification(
        self, request: SetTaskPushNotificationConfigRequest
    ) -> SetTaskPushNotificationConfigResponse:
        pass

    @abstractmethod
    async def on_get_task_push_notification(
        self, request: GetTaskPushNotificationConfigRequest
    ) -> GetTaskPushNotificationConfigResponse:
        pass

    @abstractmethod
    async def on_resubscribe_to_task(
        self, request: TaskResubscriptionRequest
    ) -> AsyncGenerator[SendMessageStreamingResponse, None]:
        yield SendMessageStreamingResponse(
            root=JSONRPCErrorResponse(
                id=request.id, error=UnsupportedOperationError()
            )
        )


class DefaultA2ARequestHandler(A2ARequestHandler):
    """Default request handler for all incoming requests."""

    def __init__(
        self, agent_executor: AgentExecutor, task_store: TaskStore | None = None
    ) -> None:
        self.agent_executor = agent_executor
        self.task_store = task_store or InMemoryTaskStore()
        self.background_streaming_tasks: set[asyncio.Task[None]] = set()

    def _build_error_response(
        self, request_id: str | int | None, error: A2AError | JSONRPCError
    ) -> JSONRPCErrorResponse:
        """Helper method to build a JSONRPCErrorResponse."""
        return JSONRPCErrorResponse(
            id=request_id,
            error=error.root if isinstance(error, A2AError) else error,
        )

    async def on_get_task(self, request: GetTaskRequest) -> GetTaskResponse:
        """Default handler for 'tasks/get'."""
        task_query_params: TaskQueryParams = request.params
        task: Task | None = await self.task_store.get(task_query_params.id)
        if not task:
            return GetTaskResponse(
                root=self._build_error_response(
                    request.id, A2AError(root=TaskNotFoundError())
                )
            )
        return GetTaskResponse(
            root=GetTaskSuccessResponse(id=request.id, result=task)
        )

    async def on_cancel_task(
        self, request: CancelTaskRequest
    ) -> CancelTaskResponse:
        """Default handler for 'tasks/cancel'."""
        task_id_params: TaskIdParams = request.params
        task: Task | None = await self.task_store.get(task_id_params.id)
        if not task:
            return CancelTaskResponse(
                root=self._build_error_response(
                    request.id, A2AError(root=TaskNotFoundError())
                )
            )

        response: CancelTaskResponse = await self.agent_executor.on_cancel(
            request, task
        )

        if isinstance(response.root, CancelTaskSuccessResponse):
            await self.task_store.save(response.root.result)

        return response

    async def on_message_send(
        self, request: SendMessageRequest
    ) -> SendMessageResponse:
        """Default handler for 'message/send'."""
        message_send_params: MessageSendParams = request.params

        task: Task | None = None
        if message_send_params.message.taskId:
            task = await self.task_store.get(message_send_params.message.taskId)
            self._append_message_to_task(message_send_params, task)

        response: SendMessageResponse = (
            await self.agent_executor.on_message_send(request, task)
        )

        if isinstance(response.root, SendMessageSuccessResponse) and isinstance(
            response.root.result, Task
        ):
            task = response.root.result
            await self.task_store.save(task)

        return response

    async def on_message_send_stream(  # type: ignore
        self,
        request: SendMessageStreamingRequest,
    ) -> AsyncGenerator[SendMessageStreamingResponse, None]:
        """Default handler for 'message/sendStream'."""
        message_send_params: MessageSendParams = request.params

        task: Task | None = None
        if message_send_params.message.taskId:
            task = await self.task_store.get(message_send_params.message.taskId)

        return self._setup_sse_consumer(task, request)

    async def on_set_task_push_notification(
        self, request: SetTaskPushNotificationConfigRequest
    ) -> SetTaskPushNotificationConfigResponse:
        """Default handler for 'tasks/pushNotificationConfig/set'."""
        return SetTaskPushNotificationConfigResponse(
            root=self._build_error_response(
                request.id, A2AError(root=UnsupportedOperationError())
            )
        )

    async def on_get_task_push_notification(
        self, request: GetTaskPushNotificationConfigRequest
    ) -> GetTaskPushNotificationConfigResponse:
        """Default handler for 'tasks/pushNotificationConfig/get'."""
        return GetTaskPushNotificationConfigResponse(
            root=self._build_error_response(
                request.id, A2AError(root=UnsupportedOperationError())
            )
        )

    async def on_resubscribe_to_task(  # type: ignore
        self, request: TaskResubscriptionRequest
    ) -> AsyncGenerator[SendMessageStreamingResponse, None]:
        """Default handler for 'tasks/resubscribe'."""
        task_id_params: TaskIdParams = request.params
        task: Task | None = await self.task_store.get(task_id_params.id)

        return self._setup_sse_consumer(task, request)

    async def _setup_sse_consumer(
        self,
        task: Task | None,
        request: TaskResubscriptionRequest | SendMessageStreamingRequest,
    ) -> AsyncGenerator[SendMessageStreamingResponse, None]:
        # create a sse_queue that allows streaming responses back to the user
        sse_queue: StreamingResponseQueue = StreamingResponseQueue()

        # spawn a task for running the streaming agent
        streaming_task = asyncio.create_task(
            self._execute_streaming_agent_task(sse_queue, task, request)
        )
        # RUF006 - requires saving a reference to the asyncio.task to prevent GC
        self.background_streaming_tasks.add(streaming_task)
        streaming_task.add_done_callback(
            self.background_streaming_tasks.discard
        )

        while True:
            event: SendMessageStreamingResponse = (
                await sse_queue.dequeue_event()
            )
            yield event
            # end the stream on error or TaskStatusUpdateEvent.final = true or Message.final = true
            if isinstance(event.root, JSONRPCErrorResponse) or (
                (
                    isinstance(event.root.result, TaskStatusUpdateEvent)
                    and event.root.result.final
                )
                or (
                    isinstance(event.root.result, Message)
                    and event.root.result.final
                )
            ):
                break

    async def _execute_streaming_agent_task(
        self,
        sse_queue: StreamingResponseQueue,
        task: Task | None,
        request: TaskResubscriptionRequest | SendMessageStreamingRequest,
    ) -> None:
        """Background task to run agent streaming."""
        try:
            if isinstance(request, TaskResubscriptionRequest):
                if not task:
                    invalid_task_event = SendMessageStreamingResponse(
                        root=self._build_error_response(
                            request.id, A2AError(root=TaskNotFoundError())
                        )
                    )
                    sse_queue.enqueue_event(invalid_task_event)
                    return
                agent_response: AsyncGenerator[
                    SendMessageStreamingResponse, None
                ] = self.agent_executor.on_resubscribe(request, task)  # type: ignore
            else:
                agent_response = self.agent_executor.on_message_stream(  # type: ignore
                    request, task
                )

            async for response in agent_response:
                response_root = response.root
                if isinstance(
                    response_root, SendMessageStreamingSuccessResponse
                ):
                    task_event = response_root.result
                    if isinstance(
                        task_event,
                        TaskStatusUpdateEvent | TaskArtifactUpdateEvent,
                    ):
                        task = await self.task_store.get(task_event.taskId)

                    if task and isinstance(
                        response_root.result, TaskStatusUpdateEvent
                    ):
                        task.status = response_root.result.status
                        await self.task_store.save(task)
                    elif task and isinstance(
                        response_root.result, TaskArtifactUpdateEvent
                    ):
                        append_artifact_to_task(task, response_root.result)
                        await self.task_store.save(task)
                sse_queue.enqueue_event(response)
        except Exception as e:
            logger.error(
                f'Error during streaming task execution for task {task.id if task else "unknown"}: {e}',
                exc_info=True,
            )
            # Ensure an error response is sent back if the stream fails unexpectedly
            error_response = SendMessageStreamingResponse(
                root=JSONRPCErrorResponse(
                    id=request.id,
                    error=InternalError(message=f'Streaming failed: {e}'),
                )
            )
            sse_queue.enqueue_event(error_response)

    def _append_message_to_task(
        self, message_send_params: MessageSendParams, task: Task | None
    ) -> None:
        if task:
            if task.history:
                task.history.append(message_send_params.message)
            else:
                task.history = [message_send_params.message]
