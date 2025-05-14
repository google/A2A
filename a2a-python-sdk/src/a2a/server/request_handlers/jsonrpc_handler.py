import logging

from collections.abc import AsyncIterable

from a2a.server.request_handlers.request_handler import RequestHandler
from a2a.server.request_handlers.response_helpers import prepare_response_object
from a2a.types import (
    AgentCard,
    CancelTaskRequest,
    CancelTaskResponse,
    CancelTaskSuccessResponse,
    GetTaskPushNotificationConfigRequest,
    GetTaskPushNotificationConfigResponse,
    GetTaskPushNotificationConfigSuccessResponse,
    GetTaskRequest,
    GetTaskResponse,
    GetTaskSuccessResponse,
    InternalError,
    JSONRPCErrorResponse,
    Message,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
    SendStreamingMessageRequest,
    SendStreamingMessageResponse,
    SendStreamingMessageSuccessResponse,
    SetTaskPushNotificationConfigRequest,
    SetTaskPushNotificationConfigResponse,
    SetTaskPushNotificationConfigSuccessResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskNotFoundError,
    TaskPushNotificationConfig,
    TaskResubscriptionRequest,
    TaskStatusUpdateEvent,
)
from a2a.utils.errors import ServerError
from a2a.utils.helpers import validate


logger = logging.getLogger(__name__)


class JSONRPCHandler:
    """A handler that maps the JSONRPC Objects to the request handler and back."""

    def __init__(
        self,
        agent_card: AgentCard,
        request_handler: RequestHandler,
    ):
        """Initializes the HttpProducer.

        Args:
            agent_card: The AgentCard describing the agent's capabilities.
            request_handler: The handler instance responsible for processing A2A requests.
        """
        self.agent_card = agent_card
        self.request_handler = request_handler

    # message/send
    async def on_message_send(
        self, request: SendMessageRequest
    ) -> SendMessageResponse:
        # TODO: Wrap in error handler to return error states
        try:
            task_or_message = await self.request_handler.on_message_send(
                request.params
            )
            return prepare_response_object(
                request.id,
                task_or_message,
                (Task, Message),
                SendMessageSuccessResponse,
                SendMessageResponse,
            )
        except ServerError as e:
            return SendMessageResponse(
                root=JSONRPCErrorResponse(
                    id=request.id, error=e.error if e.error else InternalError()
                )
            )

    # message/stream
    @validate(
        lambda self: self.agent_card.capabilities.streaming,
        'Streaming is not supported by the agent',
    )
    async def on_message_send_stream(
        self, request: SendStreamingMessageRequest
    ) -> AsyncIterable[SendStreamingMessageResponse]:
        try:
            async for event in self.request_handler.on_message_send_stream(
                request.params
            ):
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
        except ServerError as e:
            yield SendStreamingMessageResponse(
                root=JSONRPCErrorResponse(
                    id=request.id, error=e.error if e.error else InternalError()
                )
            )

    # tasks/cancel
    async def on_cancel_task(
        self, request: CancelTaskRequest
    ) -> CancelTaskResponse:
        try:
            task = await self.request_handler.on_cancel_task(request.params)
            if task:
                return prepare_response_object(
                    request.id,
                    task,
                    (Task,),
                    CancelTaskSuccessResponse,
                    CancelTaskResponse,
                )
            raise ServerError(error=TaskNotFoundError())
        except ServerError as e:
            return CancelTaskResponse(
                root=JSONRPCErrorResponse(
                    id=request.id, error=e.error if e.error else InternalError()
                )
            )

    # tasks/resubscribe
    async def on_resubscribe_to_task(
        self, request: TaskResubscriptionRequest
    ) -> AsyncIterable[SendStreamingMessageResponse]:
        try:
            async for event in self.request_handler.on_resubscribe_to_task(
                request.params
            ):
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
        except ServerError as e:
            yield SendStreamingMessageResponse(
                root=JSONRPCErrorResponse(
                    id=request.id, error=e.error if e.error else InternalError()
                )
            )

    # tasks/pushNotification/get
    async def get_push_notification(
        self, request: GetTaskPushNotificationConfigRequest
    ) -> GetTaskPushNotificationConfigResponse:
        try:
            config = (
                await self.request_handler.on_get_task_push_notification_config(
                    request.params
                )
            )
            return prepare_response_object(
                request.id,
                config,
                (TaskPushNotificationConfig,),
                GetTaskPushNotificationConfigSuccessResponse,
                GetTaskPushNotificationConfigResponse,
            )
        except ServerError as e:
            return GetTaskPushNotificationConfigResponse(
                root=JSONRPCErrorResponse(
                    id=request.id, error=e.error if e.error else InternalError()
                )
            )

    # tasks/pushNotification/set
    @validate(
        lambda self: self.agent_card.capabilities.pushNotifications,
        'Push notifications are not supported by the agent',
    )
    async def set_push_notification(
        self, request: SetTaskPushNotificationConfigRequest
    ) -> SetTaskPushNotificationConfigResponse:
        try:
            config = (
                await self.request_handler.on_set_task_push_notification_config(
                    request.params
                )
            )
            return prepare_response_object(
                request.id,
                config,
                (TaskPushNotificationConfig,),
                SetTaskPushNotificationConfigSuccessResponse,
                SetTaskPushNotificationConfigResponse,
            )
        except ServerError as e:
            return SetTaskPushNotificationConfigResponse(
                root=JSONRPCErrorResponse(
                    id=request.id, error=e.error if e.error else InternalError()
                )
            )

    # tasks/get
    async def on_get_task(self, request: GetTaskRequest) -> GetTaskResponse:
        try:
            task = await self.request_handler.on_get_task(request.params)
            if task:
                return prepare_response_object(
                    request.id,
                    task,
                    (Task,),
                    GetTaskSuccessResponse,
                    GetTaskResponse,
                )
            raise ServerError(error=TaskNotFoundError())
        except ServerError as e:
            return GetTaskResponse(
                root=JSONRPCErrorResponse(
                    id=request.id, error=e.error if e.error else InternalError()
                )
            )
