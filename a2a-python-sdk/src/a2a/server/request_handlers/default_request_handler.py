import asyncio
import logging

from collections.abc import AsyncGenerator

from a2a.server.agent_execution import AgentExecutor
from a2a.server.events import EventConsumer, EventQueue
from a2a.server.request_handlers.request_handler import A2ARequestHandler
from a2a.server.request_handlers.response_helpers import (
    build_error_response,
    prepare_response_object,
)
from a2a.server.tasks import InMemoryTaskStore, TaskManager, TaskStore
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
    Message,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
    SendStreamingMessageRequest,
    SendStreamingMessageResponse,
    SendStreamingMessageSuccessResponse,
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


logger = logging.getLogger(__name__)


class DefaultA2ARequestHandler(A2ARequestHandler):
    """Default request handler for all incoming requests."""

    def __init__(
        self, agent_executor: AgentExecutor, task_store: TaskStore | None = None
    ) -> None:
        self.agent_executor = agent_executor
        self.task_store = task_store or InMemoryTaskStore()

    async def on_get_task(self, request: GetTaskRequest) -> GetTaskResponse:
        """Default handler for 'tasks/get'."""
        task_query_params: TaskQueryParams = request.params

        task: Task | None = await self.task_store.get(task_query_params.id)
        if not task:
            return build_error_response(
                request.id, A2AError(TaskNotFoundError()), GetTaskResponse
            )

        return prepare_response_object(
            request.id,
            task,
            (Task,),
            GetTaskSuccessResponse,
            GetTaskResponse,
        )

    async def on_cancel_task(
        self, request: CancelTaskRequest
    ) -> CancelTaskResponse:
        """Default handler for 'tasks/cancel'."""
        task_id_params: TaskIdParams = request.params
        task: Task | None = await self.task_store.get(task_id_params.id)
        if not task:
            return build_error_response(
                request.id,
                A2AError(TaskNotFoundError()),
                CancelTaskResponse,
            )

        task_manager = TaskManager(
            task_id=task.id,
            context_id=task.contextId,
            task_store=self.task_store,
        )

        queue = EventQueue()
        await self.agent_executor.on_cancel(request, queue, task)

        consumer = EventConsumer(queue, task_manager)
        result = await consumer.consume_one()

        return prepare_response_object(
            request.id,
            result,
            (Task,),
            CancelTaskSuccessResponse,
            CancelTaskResponse,
        )

    async def on_message_send(
        self, request: SendMessageRequest
    ) -> SendMessageResponse:
        """Default handler for 'message/send'."""
        message_send_params: MessageSendParams = request.params

        task_manager = TaskManager(
            task_id=message_send_params.message.taskId,
            context_id=message_send_params.message.contextId,
            task_store=self.task_store,
        )
        task: Task | None = await task_manager.get_task()
        if task:
            await self._append_message_to_task(message_send_params, task)

        queue = EventQueue()
        await self.agent_executor.on_message_send(request, queue, task)

        consumer = EventConsumer(queue, task_manager)
        result = await consumer.consume_one()

        return prepare_response_object(
            request.id,
            result,
            (Task, Message),
            SendMessageSuccessResponse,
            SendMessageResponse,
        )

    async def on_message_send_stream(
        self,
        request: SendStreamingMessageRequest,
    ) -> AsyncGenerator[SendStreamingMessageResponse, None]:
        """Default handler for 'message/stream'."""
        message_send_params: MessageSendParams = request.params

        task_manager = TaskManager(
            task_id=message_send_params.message.taskId,
            context_id=message_send_params.message.contextId,
            task_store=self.task_store,
        )
        task: Task | None = await task_manager.get_task()
        if task:
            await self._append_message_to_task(message_send_params, task)

        event_queue = EventQueue()
        consumer = EventConsumer(event_queue, task_manager)

        producer_task_name = f'agent-message-stream-{request.id}-{message_send_params.message.taskId}'
        producer_task = asyncio.create_task(
            self.agent_executor.on_message_stream(request, event_queue, task),
            name=producer_task_name,
        )

        try:
            async for event in consumer.consume_all():
                yield prepare_response_object(
                    request.id,
                    event,
                    (
                        Task,
                        Message,
                        TaskArtifactUpdateEvent,
                        TaskStatusUpdateEvent,
                    ),
                    SendStreamingMessageSuccessResponse,
                    SendStreamingMessageResponse,
                )
        finally:
            if not producer_task.done():
                producer_task.cancel()
                try:
                    await producer_task
                except asyncio.CancelledError:
                    logger.info(
                        'Agent message stream task was cancelled: %s',
                        producer_task_name,
                    )
                except Exception as e:
                    logger.exception(
                        'Error in agent message stream task %s: %s',
                        producer_task_name,
                        e,
                    )

    async def on_set_task_push_notification_config(
        self, request: SetTaskPushNotificationConfigRequest
    ) -> SetTaskPushNotificationConfigResponse:
        """Default handler for 'tasks/pushNotificationConfig/set'."""
        return build_error_response(
            request.id,
            A2AError(UnsupportedOperationError()),
            SetTaskPushNotificationConfigResponse,
        )

    async def on_get_task_push_notification_config(
        self, request: GetTaskPushNotificationConfigRequest
    ) -> GetTaskPushNotificationConfigResponse:
        """Default handler for 'tasks/pushNotificationConfig/get'."""
        return build_error_response(
            request.id,
            A2AError(UnsupportedOperationError()),
            GetTaskPushNotificationConfigResponse,
        )

    async def on_resubscribe_to_task(
        self, request: TaskResubscriptionRequest
    ) -> AsyncGenerator[SendStreamingMessageResponse, None]:
        """Default handler for 'tasks/resubscribe'."""
        task_id_params: TaskIdParams = request.params

        task: Task | None = await self.task_store.get(task_id_params.id)
        if not task:
            yield build_error_response(
                request.id,
                A2AError(TaskNotFoundError()),
                SendStreamingMessageResponse,
            )
            return

        task_manager = TaskManager(
            task_id=task.id,
            context_id=task.contextId,
            task_store=self.task_store,
        )

        event_queue = EventQueue()
        consumer = EventConsumer(event_queue, task_manager)

        producer_task_name = f'agent-resubscribe-stream-{request.id}-{task.id}'
        producer_task = asyncio.create_task(
            self.agent_executor.on_resubscribe(request, event_queue, task),
            name=producer_task_name,
        )

        try:
            async for event in consumer.consume_all():
                yield prepare_response_object(
                    request.id,
                    event,
                    (
                        Task,
                        Message,
                        TaskArtifactUpdateEvent,
                        TaskStatusUpdateEvent,
                    ),
                    SendStreamingMessageSuccessResponse,
                    SendStreamingMessageResponse,
                )
        finally:
            if not producer_task.done():
                producer_task.cancel()
            try:
                await producer_task
            except asyncio.CancelledError:
                logger.info(
                    'Agent resubscribe task was cancelled: %s',
                    producer_task_name,
                )
            except Exception as e:
                logger.exception(
                    'Error in agent resubscribe task %s: %s',
                    producer_task_name,
                    e,
                )

    async def _append_message_to_task(
        self, message_send_params: MessageSendParams, task: Task
    ) -> None:
        if task.history:
            task.history.append(message_send_params.message)
        else:
            task.history = [message_send_params.message]

        await self.task_store.save(task)
