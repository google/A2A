from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from a2a.types import (
    CancelTaskRequest,
    CancelTaskResponse,
    GetTaskPushNotificationConfigRequest,
    GetTaskPushNotificationConfigResponse,
    GetTaskRequest,
    GetTaskResponse,
    JSONRPCErrorResponse,
    SendMessageRequest,
    SendMessageResponse,
    SendStreamingMessageRequest,
    SendStreamingMessageResponse,
    SetTaskPushNotificationConfigRequest,
    SetTaskPushNotificationConfigResponse,
    TaskResubscriptionRequest,
    UnsupportedOperationError,
)


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
        self, request: SendStreamingMessageRequest
    ) -> AsyncGenerator[SendStreamingMessageResponse, None]:
        yield SendStreamingMessageResponse(
            JSONRPCErrorResponse(
                id=request.id, error=UnsupportedOperationError()
            )
        )

    @abstractmethod
    async def on_set_task_push_notification_config(
        self, request: SetTaskPushNotificationConfigRequest
    ) -> SetTaskPushNotificationConfigResponse:
        pass

    @abstractmethod
    async def on_get_task_push_notification_config(
        self, request: GetTaskPushNotificationConfigRequest
    ) -> GetTaskPushNotificationConfigResponse:
        pass

    @abstractmethod
    async def on_resubscribe_to_task(
        self, request: TaskResubscriptionRequest
    ) -> AsyncGenerator[SendStreamingMessageResponse, None]:
        yield SendStreamingMessageResponse(
            JSONRPCErrorResponse(
                id=request.id, error=UnsupportedOperationError()
            )
        )
