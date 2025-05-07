from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, Union
from typing_extensions import Self
from uuid import uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    field_serializer,
    model_validator,
)

from .types_fingerprint import Fingerprint, MessageVerification


class TaskState(str, Enum):
    SUBMITTED = 'submitted'
    WORKING = 'working'
    INPUT_REQUIRED = 'input-required'
    COMPLETED = 'completed'
    CANCELED = 'canceled'
    FAILED = 'failed'
    UNKNOWN = 'unknown'


class TextPart(BaseModel):
    type: Literal['text'] = 'text'
    text: str
    metadata: Optional[Dict[str, Any]] = None


class FileContent(BaseModel):
    name: Optional[str] = None
    mimeType: Optional[str] = None
    bytes: Optional[str] = None
    uri: Optional[str] = None

    @model_validator(mode='after')
    def check_content(self) -> Self:
        if not (self.bytes or self.uri):
            raise ValueError(
                "Either 'bytes' or 'uri' must be present in the file data"
            )
        if self.bytes and self.uri:
            raise ValueError(
                "Only one of 'bytes' or 'uri' can be present in the file data"
            )
        return self


class FilePart(BaseModel):
    type: Literal['file'] = 'file'
    file: FileContent
    metadata: Optional[Dict[str, Any]] = None


class DataPart(BaseModel):
    type: Literal['data'] = 'data'
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


Part = Annotated[Union[TextPart, FilePart, DataPart], Field(discriminator='type')]


class Message(BaseModel):
    role: Literal['user', 'agent']
    parts: List[Part]
    metadata: Optional[Dict[str, Any]] = None
    verification: Optional[MessageVerification] = None


class TaskStatus(BaseModel):
    state: TaskState
    message: Optional[Message] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_serializer('timestamp')
    def serialize_dt(self, dt: datetime, _info):
        return dt.isoformat()


class Artifact(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parts: List[Part]
    metadata: Optional[Dict[str, Any]] = None
    index: int = 0
    append: Optional[bool] = None
    lastChunk: Optional[bool] = None


class Task(BaseModel):
    id: str
    sessionId: Optional[str] = None
    status: TaskStatus
    artifacts: Optional[List[Artifact]] = None
    history: Optional[List[Message]] = None
    metadata: Optional[Dict[str, Any]] = None


class TaskStatusUpdateEvent(BaseModel):
    id: str
    status: TaskStatus
    final: bool = False
    metadata: Optional[Dict[str, Any]] = None


class TaskArtifactUpdateEvent(BaseModel):
    id: str
    artifact: Artifact
    metadata: Optional[Dict[str, Any]] = None


class AuthenticationInfo(BaseModel):
    model_config = ConfigDict(extra='allow')

    schemes: List[str]
    credentials: Optional[str] = None


class PushNotificationConfig(BaseModel):
    url: str
    token: Optional[str] = None
    authentication: Optional[AuthenticationInfo] = None


class TaskIdParams(BaseModel):
    id: str
    metadata: Optional[Dict[str, Any]] = None


class TaskQueryParams(TaskIdParams):
    historyLength: Optional[int] = None


class TaskSendParams(BaseModel):
    id: str
    sessionId: str = Field(default_factory=lambda: uuid4().hex)
    message: Message
    acceptedOutputModes: Optional[List[str]] = None
    pushNotification: Optional[PushNotificationConfig] = None
    historyLength: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class TaskPushNotificationConfig(BaseModel):
    id: str
    pushNotificationConfig: PushNotificationConfig


## RPC Messages


class JSONRPCMessage(BaseModel):
    jsonrpc: Literal['2.0'] = '2.0'
    id: Optional[Union[int, str]] = Field(default_factory=lambda: uuid4().hex)


class JSONRPCRequest(JSONRPCMessage):
    method: str
    params: Optional[Dict[str, Any]] = None


class JSONRPCError(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None


class JSONRPCResponse(JSONRPCMessage):
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None


class SendTaskRequest(JSONRPCRequest):
    method: Literal['tasks/send'] = 'tasks/send'
    params: TaskSendParams


class SendTaskResponse(JSONRPCResponse):
    result: Optional[Task] = None


class SendTaskStreamingRequest(JSONRPCRequest):
    method: Literal['tasks/sendSubscribe'] = 'tasks/sendSubscribe'
    params: TaskSendParams


class SendTaskStreamingResponse(JSONRPCResponse):
    result: Optional[Union[TaskStatusUpdateEvent, TaskArtifactUpdateEvent]] = None


class GetTaskRequest(JSONRPCRequest):
    method: Literal['tasks/get'] = 'tasks/get'
    params: TaskQueryParams


class GetTaskResponse(JSONRPCResponse):
    result: Optional[Task] = None


class CancelTaskRequest(JSONRPCRequest):
    method: Literal['tasks/cancel',] = 'tasks/cancel'
    params: TaskIdParams


class CancelTaskResponse(JSONRPCResponse):
    result: Optional[Task] = None


class SetTaskPushNotificationRequest(JSONRPCRequest):
    method: Literal['tasks/pushNotification/set',] = (
        'tasks/pushNotification/set'
    )
    params: TaskPushNotificationConfig


class SetTaskPushNotificationResponse(JSONRPCResponse):
    result: Optional[TaskPushNotificationConfig] = None


class GetTaskPushNotificationRequest(JSONRPCRequest):
    method: Literal['tasks/pushNotification/get',] = (
        'tasks/pushNotification/get'
    )
    params: TaskIdParams


class GetTaskPushNotificationResponse(JSONRPCResponse):
    result: Optional[TaskPushNotificationConfig] = None


class TaskResubscriptionRequest(JSONRPCRequest):
    method: Literal['tasks/resubscribe',] = 'tasks/resubscribe'
    params: TaskIdParams


A2ARequest = TypeAdapter(
    Annotated[
        Union[
            SendTaskRequest,
            GetTaskRequest,
            CancelTaskRequest,
            SetTaskPushNotificationRequest,
            GetTaskPushNotificationRequest,
            TaskResubscriptionRequest,
            SendTaskStreamingRequest,
        ],
        Field(discriminator='method'),
    ]
)

## Error types


class JSONParseError(JSONRPCError):
    code: int = -32700
    message: str = 'Invalid JSON payload'
    data: Optional[Any] = None


class InvalidRequestError(JSONRPCError):
    code: int = -32600
    message: str = 'Request payload validation error'
    data: Optional[Any] = None


class MethodNotFoundError(JSONRPCError):
    code: int = -32601
    message: str = 'Method not found'
    data: None = None


class InvalidParamsError(JSONRPCError):
    code: int = -32602
    message: str = 'Invalid parameters'
    data: Optional[Any] = None


class InternalError(JSONRPCError):
    code: int = -32603
    message: str = 'Internal error'
    data: Optional[Any] = None


class TaskNotFoundError(JSONRPCError):
    code: int = -32001
    message: str = 'Task not found'
    data: None = None


class TaskNotCancelableError(JSONRPCError):
    code: int = -32002
    message: str = 'Task cannot be canceled'
    data: None = None


class PushNotificationNotSupportedError(JSONRPCError):
    code: int = -32003
    message: str = 'Push Notification is not supported'
    data: None = None


class UnsupportedOperationError(JSONRPCError):
    code: int = -32004
    message: str = 'This operation is not supported'
    data: None = None


class ContentTypeNotSupportedError(JSONRPCError):
    code: int = -32005
    message: str = 'Incompatible content types'
    data: None = None


class AgentProvider(BaseModel):
    organization: str
    url: Optional[str] = None


class AgentCapabilities(BaseModel):
    streaming: bool = False
    pushNotifications: bool = False
    stateTransitionHistory: bool = False


class AgentAuthentication(BaseModel):
    schemes: List[str]
    credentials: Optional[str] = None
    fingerprint: Optional[Fingerprint] = None


class AgentSkill(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    examples: Optional[List[str]] = None
    inputModes: Optional[List[str]] = None
    outputModes: Optional[List[str]] = None


class AgentCard(BaseModel):
    name: str
    description: Optional[str] = None
    url: str
    provider: Optional[AgentProvider] = None
    version: str
    documentationUrl: Optional[str] = None
    capabilities: AgentCapabilities
    authentication: Optional[AgentAuthentication] = None
    defaultInputModes: List[str] = ['text']
    defaultOutputModes: List[str] = ['text']
    skills: List[AgentSkill]
    fingerprint: Optional[Fingerprint] = None


class A2AClientError(Exception):
    pass


class A2AClientHTTPError(A2AClientError):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f'HTTP Error {status_code}: {message}')


class A2AClientJSONError(A2AClientError):
    def __init__(self, message: str):
        self.message = message
        super().__init__(f'JSON Error: {message}')


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""


class FingerprintVerificationError(Exception):
    """Exception for fingerprint verification failures."""
    
    def __init__(self, message: str = "Fingerprint verification failed"):
        self.message = message
        super().__init__(message)