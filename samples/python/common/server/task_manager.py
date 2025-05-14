from abc import ABC, abstractmethod
from typing import Union, AsyncIterable, List, Tuple
from common.types import Task
from common.types import (
    JSONRPCResponse,
    TaskIdParams,
    TaskQueryParams,
    GetTaskRequest,
    TaskNotFoundError,
    CancelTaskRequest,
    TaskNotCancelableError,
    SetTaskPushNotificationRequest,
    GetTaskPushNotificationRequest,
    GetTaskResponse,
    CancelTaskResponse,
    SetTaskPushNotificationResponse,
    GetTaskPushNotificationResponse,
    TaskStatus,
    TaskState,
    TaskResubscriptionRequest,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageStreamRequest,
    SendMessageStreamResponse,
    Artifact,
    PushNotificationConfig,
    TaskStatusUpdateEvent,
    JSONRPCError,
    TaskPushNotificationConfig,
    InternalError,
    Message,
    GetAuthenticatedExtendedCardRequest,
    GetAuthenticatedExtendedCardResponse,
    UnsupportedOperationError,
    AgentCard,
    InvalidRequestError,
    AgentSkill,
    TextPart,
    InvalidParamsError,
)
import common.server.utils as utils
import asyncio
from starlette.requests import Request
import logging
import uuid

logger = logging.getLogger(__name__)


class TaskManager(ABC):
    @abstractmethod
    async def on_get_task(self, request: GetTaskRequest) -> GetTaskResponse:
        pass

    @abstractmethod
    async def on_cancel_task(
        self, request: CancelTaskRequest
    ) -> CancelTaskResponse:
        pass

    @abstractmethod
    async def on_send_message(
        self, request: SendMessageRequest
    ) -> SendMessageResponse:
        pass

    @abstractmethod
    async def on_send_message_stream(
        self, request: SendMessageStreamRequest
    ) -> Union[AsyncIterable[SendMessageStreamResponse], JSONRPCResponse]:
        pass

    @abstractmethod
    async def on_set_task_push_notification(
        self, request: SetTaskPushNotificationRequest
    ) -> SetTaskPushNotificationResponse:
        pass

    @abstractmethod
    async def on_get_task_push_notification(
        self, request: GetTaskPushNotificationRequest
    ) -> GetTaskPushNotificationResponse:
        pass

    @abstractmethod
    async def on_resubscribe_to_task(
        self, request: TaskResubscriptionRequest
    ) -> AsyncIterable[SendMessageStreamResponse] | JSONRPCResponse:
        pass

    @abstractmethod
    async def on_get_authenticated_extended_card(
        self, http_request: Request, rpc_request: GetAuthenticatedExtendedCardRequest, base_agent_card: AgentCard
    ) -> GetAuthenticatedExtendedCardResponse:
        pass


class InMemoryTaskManager(TaskManager):
    def __init__(self):
        self.tasks: dict[str, Task] = {}
        self.push_notification_infos: dict[str, PushNotificationConfig] = {}
        self.lock = asyncio.Lock()
        self.task_sse_subscribers: dict[str, list[asyncio.Queue]] = {}
        self.subscriber_lock = asyncio.Lock()

    async def on_get_task(self, request: GetTaskRequest) -> GetTaskResponse:
        logger.info(f'Getting task {request.params.id}')
        task_query_params: TaskQueryParams = request.params

        async with self.lock:
            task = self.tasks.get(task_query_params.id)
            if task is None:
                return GetTaskResponse(id=request.id, error=TaskNotFoundError())

            task_result = self.append_task_history(
                task, task_query_params.historyLength
            )

        return GetTaskResponse(id=request.id, result=task_result)

    async def on_cancel_task(
        self, request: CancelTaskRequest
    ) -> CancelTaskResponse:
        logger.info(f'Cancelling task {request.params.id}')
        task_id_params: TaskIdParams = request.params

        async with self.lock:
            task = self.tasks.get(task_id_params.id)
            if task is None:
                return CancelTaskResponse(
                    id=request.id, error=TaskNotFoundError()
                )

        return CancelTaskResponse(id=request.id, error=TaskNotCancelableError())

    @abstractmethod
    async def on_send_message(
        self, request: SendMessageRequest
    ) -> SendMessageResponse:
        pass

    @abstractmethod
    async def on_send_message_stream(
        self, request: SendMessageStreamRequest
    ) -> Union[AsyncIterable[SendMessageStreamResponse], JSONRPCResponse]:
        pass

    async def set_push_notification_info(
        self, task_id: str, notification_config: PushNotificationConfig
    ):
        async with self.lock:
            task = self.tasks.get(task_id)
            if task is None:
                raise ValueError(f'Task not found for {task_id}')

            self.push_notification_infos[task_id] = notification_config

        return

    async def get_push_notification_info(
        self, task_id: str
    ) -> PushNotificationConfig:
        async with self.lock:
            task = self.tasks.get(task_id)
            if task is None:
                raise ValueError(f'Task not found for {task_id}')

            return self.push_notification_infos[task_id]

        return

    async def has_push_notification_info(self, task_id: str) -> bool:
        async with self.lock:
            return task_id in self.push_notification_infos

    async def on_set_task_push_notification(
        self, request: SetTaskPushNotificationRequest
    ) -> SetTaskPushNotificationResponse:
        logger.info(f'Setting task push notification {request.params.id}')
        task_notification_params: TaskPushNotificationConfig = request.params

        try:
            await self.set_push_notification_info(
                task_notification_params.id,
                task_notification_params.pushNotificationConfig,
            )
        except Exception as e:
            logger.error(f'Error while setting push notification info: {e}')
            return JSONRPCResponse(
                id=request.id,
                error=InternalError(
                    message='An error occurred while setting push notification info'
                ),
            )

        return SetTaskPushNotificationResponse(
            id=request.id, result=task_notification_params
        )

    async def on_get_task_push_notification(
        self, request: GetTaskPushNotificationRequest
    ) -> GetTaskPushNotificationResponse:
        logger.info(f'Getting task push notification {request.params.id}')
        task_params: TaskIdParams = request.params

        try:
            notification_info = await self.get_push_notification_info(
                task_params.id
            )
        except Exception as e:
            logger.error(f'Error while getting push notification info: {e}')
            return GetTaskPushNotificationResponse(
                id=request.id,
                error=InternalError(
                    message='An error occurred while getting push notification info'
                ),
            )

        return GetTaskPushNotificationResponse(
            id=request.id,
            result=TaskPushNotificationConfig(
                id=task_params.id, pushNotificationConfig=notification_info
            ),
        )

    async def upsert_task(
        self, params: MessageSendParams
    ) -> Task:
        taskId, contextId = self._extract_task_and_context(params)
        # Ensure consistency now
        params.message.taskId = taskId
        params.message.contextId = contextId
        async with self.lock:
            task = self.tasks.get(taskId, None)
            if task is None:
                task = Task(
                    id=taskId,
                    contextId=contextId,
                    messages=[params.message],
                    status=TaskStatus(state=TaskState.SUBMITTED),
                    history=[params.message],
                )
                self.tasks[taskId] = task
            else:
                task.history.append(params.message)

            return task

    async def on_resubscribe_to_task(
        self, request: TaskResubscriptionRequest
    ) -> Union[AsyncIterable[SendMessageStreamResponse], JSONRPCResponse]:
        return utils.new_not_implemented_error(request.id)

    async def update_store(
        self, task_id: str, status: TaskStatus, artifacts: list[Artifact]
    ) -> Task:
        async with self.lock:
            try:
                task = self.tasks[task_id]
            except KeyError:
                logger.error(f'Task {task_id} not found for updating the task')
                raise ValueError(f'Task {task_id} not found')

            task.status = status

            if status.message is not None:
                task.history.append(status.message)

            if artifacts is not None:
                if task.artifacts is None:
                    task.artifacts = []
                task.artifacts.extend(artifacts)

            return task

    def append_task_history(self, task: Task, historyLength: int | None):
        new_task = task.model_copy()
        if historyLength is not None and historyLength > 0:
            new_task.history = new_task.history[-historyLength:]
        else:
            new_task.history = []

        return new_task

    async def setup_sse_consumer(
        self, task_id: str, is_resubscribe: bool = False
    ):
        async with self.subscriber_lock:
            if task_id not in self.task_sse_subscribers:
                if is_resubscribe:
                    raise ValueError('Task not found for resubscription')
                else:
                    self.task_sse_subscribers[task_id] = []

            sse_event_queue = asyncio.Queue(maxsize=0)  # <=0 is unlimited
            self.task_sse_subscribers[task_id].append(sse_event_queue)
            return sse_event_queue

    async def enqueue_events_for_sse(self, task_id, task_update_event):
        async with self.subscriber_lock:
            if task_id not in self.task_sse_subscribers:
                return

            current_subscribers = self.task_sse_subscribers[task_id]
            for subscriber in current_subscribers:
                await subscriber.put(task_update_event)

    async def dequeue_message_events_for_sse(
        self, request_id, task_id, sse_event_queue: asyncio.Queue
    ) -> AsyncIterable[SendMessageStreamResponse] | JSONRPCResponse:
        try:
            while True:
                event = await sse_event_queue.get()
                if isinstance(event, JSONRPCError):
                    yield SendMessageStreamResponse(id=request_id, error=event)
                    break

                yield SendMessageStreamResponse(id=request_id, result=event)
                if isinstance(event, TaskStatusUpdateEvent) and event.final:
                    break
                # Other terminal state is that the event is a message
                if isinstance(event, Message):
                    break
        finally:
            async with self.subscriber_lock:
                if task_id in self.task_sse_subscribers:
                    self.task_sse_subscribers[task_id].remove(sse_event_queue)

    def _extract_task_and_context(
        self, params: MessageSendParams
    ) -> Tuple[str, str]:
        # Extract task and context id from request, if provided else generate.
        taskId = (
            params.message.taskId
            if params.message.taskId
            else str(uuid.uuid4())
        )
        contextId = (
            params.message.contextId
            if params.message.contextId
            else str(uuid.uuid4())
        )
        return taskId, contextId

    def _get_user_query(self, params: MessageSendParams) -> str:
        part = params.message.parts[0]
        if not isinstance(part, TextPart):
            raise ValueError('Only text parts are supported')
        return part.text

    def _validate_output_modes(
        self,
        request: SendMessageRequest | SendMessageStreamRequest,
        supportedTypes: List[str],
    ) -> JSONRPCResponse | None:
        acceptedOutputModes = (
            request.params.configuration.acceptedOutputModes
            if request.params.configuration
            else []
        )
        if not utils.are_modalities_compatible(
            acceptedOutputModes,
            supportedTypes,
        ):
            logger.warning(
                'Unsupported output mode. Received %s, Support %s',
                acceptedOutputModes,
                supportedTypes,
            )

    async def on_get_authenticated_extended_card(
        self, http_request: Request, rpc_request: GetAuthenticatedExtendedCardRequest, base_agent_card: AgentCard
    ) -> GetAuthenticatedExtendedCardResponse:
        # This base implementation in InMemoryTaskManager assumes authentication has been handled by a subclass or is not required.
        logger.info(f'InMemoryTaskManager: Handling GetAuthenticatedExtendedCard request: {rpc_request.id}')

        if not base_agent_card.supportsAuthenticatedExtendedCard:
            logger.warning(f"InMemoryTaskManager: Agent card (id: {base_agent_card.id if hasattr(base_agent_card, 'id') else 'N/A'}) does not support authenticated extended card.")
            return GetAuthenticatedExtendedCardResponse(
                id=rpc_request.id,
                error=UnsupportedOperationError(message="Agent does not support authenticated extended card.")
            )

        # Create a deep copy of the base agent card to modify it
        extended_card = base_agent_card.model_copy(deep=True)

        logger.info(f"InMemoryTaskManager: Returning extended agent card for request: {rpc_request.id}")
        return GetAuthenticatedExtendedCardResponse(id=rpc_request.id, result=extended_card)

    def _validate_push_config(
        self,
        request: SendMessageRequest | SendMessageStreamRequest,
    ) -> JSONRPCResponse | None:
        pushNotificationConfig = (
            request.params.configuration.pushNotification
            if request.params.configuration
            else None
        )
        if pushNotificationConfig and not pushNotificationConfig.url:
            logger.warning('Push notification URL is missing')
            return JSONRPCResponse(
                id=request.id,
                error=InvalidParamsError(
                    message='Push notification URL is missing'
                ),
            )

        return None

    async def _update_store(
        self, task_id: str, status: TaskStatus, artifacts: list[Artifact]
    ) -> Task:
        async with self.lock:
            try:
                task = self.tasks[task_id]
            except KeyError:
                logger.error(f'Task {task_id} not found for updating the task')
                raise ValueError(f'Task {task_id} not found')
            task.status = status
            if artifacts is not None:
                if task.artifacts is None:
                    task.artifacts = []
                task.artifacts.extend(artifacts)
            return task
