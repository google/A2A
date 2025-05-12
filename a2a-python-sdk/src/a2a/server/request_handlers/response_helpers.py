# response types
from typing import TypeVar

from a2a.types import (
    A2AError,
    CancelTaskResponse,
    CancelTaskSuccessResponse,
    GetTaskPushNotificationConfigResponse,
    GetTaskPushNotificationConfigSuccessResponse,
    GetTaskResponse,
    GetTaskSuccessResponse,
    InvalidAgentResponseError,
    JSONRPCError,
    JSONRPCErrorResponse,
    Message,
    SendMessageResponse,
    SendMessageSuccessResponse,
    SendStreamingMessageResponse,
    SendStreamingMessageSuccessResponse,
    SetTaskPushNotificationConfigResponse,
    SetTaskPushNotificationConfigSuccessResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
)


RT = TypeVar(
    'RT',
    GetTaskResponse,
    CancelTaskResponse,
    SendMessageResponse,
    SetTaskPushNotificationConfigResponse,
    GetTaskPushNotificationConfigResponse,
    SendStreamingMessageResponse,
)

# success types
SPT = TypeVar(
    'SPT',
    GetTaskSuccessResponse,
    CancelTaskSuccessResponse,
    SendMessageSuccessResponse,
    SetTaskPushNotificationConfigSuccessResponse,
    GetTaskPushNotificationConfigSuccessResponse,
    SendStreamingMessageSuccessResponse,
)

# result types
EventTypes = (
    Task
    | Message
    | TaskArtifactUpdateEvent
    | TaskStatusUpdateEvent
    | A2AError
    | JSONRPCError
)


def build_error_response(
    request_id: str | int | None,
    error: A2AError | JSONRPCError,
    response_wrapper_type: type[RT],
) -> RT:
    """Helper method to build a JSONRPCErrorResponse."""
    return response_wrapper_type(
        JSONRPCErrorResponse(
            id=request_id,
            error=error.root if isinstance(error, A2AError) else error,
        )
    )


def prepare_response_object(
    request_id: str | int | None,
    response: EventTypes,
    success_response_types: tuple[type, ...],
    success_payload_type: type[SPT],
    response_type: type[RT],
) -> RT:
    """Helper method to build appropriate JSONRPCResponse object for RPC methods."""
    if isinstance(response, success_response_types):
        return response_type(
            success_payload_type(id=request_id, result=response)  # type:ignore
        )

    if isinstance(response, A2AError | JSONRPCError):
        return build_error_response(request_id, response, response_type)

    # If consumer_data is not an expected success type and not an error,
    # it's an invalid type of response from the agent for this specific method.
    response = A2AError(
        InvalidAgentResponseError(
            message='Agent returned invalid type response for this method'
        )
    )

    return build_error_response(request_id, response, response_type)
