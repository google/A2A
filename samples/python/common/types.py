from datetime import datetime
from enum import Enum
from typing import Union, Any, Dict, List, Annotated, Optional, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, TypeAdapter, model_validator, ConfigDict, field_serializer
from typing_extensions import Self


# --- Core Task Related Enums and Models ---

class TaskState(str, Enum):
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"
    UNKNOWN = "unknown"


class TextPart(BaseModel):
    type: Literal["text"] = Field("text", description="Type of the part")
    text: str
    metadata: Optional[Dict[str, Any]] = None


class FileContent(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "description": "Represents the content of a file, either as base64 encoded bytes or a URI.\n\nEnsures that either 'bytes' or 'uri' is provided, but not both (enforced by application logic based on Pydantic validator)."
        }
    )
    name: Optional[str] = None
    mimeType: Optional[str] = None
    bytes: Optional[str] = Field(None, description="Base64 encoded file content.")  # JSON Schema should specify contentEncoding: base64
    uri: Optional[str] = Field(None, description="URI pointing to the file content.")  # JSON Schema should specify format: uri

    @model_validator(mode="after")
    def check_content(self) -> Self:
        if self.bytes is None and self.uri is None:
            raise ValueError("FileContent must have either 'bytes' or 'uri'")
        if self.bytes is not None and self.uri is not None:
            raise ValueError("FileContent cannot have both 'bytes' and 'uri'")
        return self


class FilePart(BaseModel):
    type: Literal["file"] = Field("file", description="Type of the part")
    file: FileContent
    metadata: Optional[Dict[str, Any]] = None


class DataPart(BaseModel):
    type: Literal["data"] = Field("data", description="Type of the part")
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


Part = Annotated[
    Union[TextPart, FilePart, DataPart],
    Field(discriminator="type", description="Represents a distinct piece of content within a Message or Artifact.")
]


class Message(BaseModel):
    role: Literal["user", "agent"]
    parts: List[Part]
    metadata: Optional[Dict[str, Any]] = None


class TaskStatus(BaseModel):
    state: TaskState
    message: Optional[Message] = Field(None, description="Optional message associated with this status update (e.g., agent response, error message).")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of when this status was recorded (ISO 8601 format).")

    @field_serializer("timestamp")
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
    artifacts: Optional[List[Artifact]] = Field(default_factory=list)
    history: Optional[List[Message]] = Field(None, description="Sequence of messages exchanged during the task execution. May be truncated.")
    metadata: Optional[Dict[str, Any]] = None


# --- Streaming Event Types ---

class TaskStatusUpdateEvent(BaseModel):
    id: str = Field(description="The ID of the task being updated.")
    status: TaskStatus
    final: bool = Field(False, description="Indicates if this is the terminal status update for the task.")
    metadata: Optional[Dict[str, Any]] = None


class TaskArtifactUpdateEvent(BaseModel):
    id: str = Field(description="The ID of the task this artifact belongs to.")
    artifact: Artifact
    metadata: Optional[Dict[str, Any]] = None


# --- Authentication and Configuration ---

class AuthenticationInfo(BaseModel):
    model_config = ConfigDict(extra="allow")
    schemes: List[str]
    credentials: Optional[str] = None


class PushNotificationConfig(BaseModel):
    url: str = Field(description="The endpoint URL for receiving push notifications.")  # JSON Schema format: uri
    token: Optional[str] = Field(None, description="Optional opaque token for simple authorization.")
    authentication: Optional[AuthenticationInfo] = None


# --- Parameter Types for Requests ---

class TaskIdParams(BaseModel):
    id: str
    metadata: Optional[Dict[str, Any]] = None


class TaskQueryParams(TaskIdParams):
    historyLength: Optional[int] = Field(None, ge=0,
                                         description="Maximum number of historical messages to include in the response. If null or 0, history is omitted.")


class TaskSendParams(BaseModel):
    id: str = Field(description="Unique identifier for the task.")
    sessionId: str = Field(default_factory=lambda: uuid4().hex,
                           description="Identifier for the session this task belongs to. Can be used to group related tasks.")
    message: Message = Field(description="The initial message initiating or continuing the task.")
    acceptedOutputModes: Optional[List[str]] = Field(None, description="MIME types the requesting agent accepts for output parts.")
    pushNotification: Optional[PushNotificationConfig] = Field(None, description="Configuration for receiving push notifications about task updates.")
    historyLength: Optional[int] = Field(None, ge=0,
                                         description="Maximum number of historical messages to include in the task response. If null or 0, history is omitted.")
    metadata: Optional[Dict[str, Any]] = None


class TaskPushNotificationConfig(BaseModel):
    id: str
    pushNotificationConfig: PushNotificationConfig


# --- JSON-RPC Base Structures ---

class JSONRPCMessage(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
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


# --- Task Specific Request/Response Types ---

class SendTaskRequest(JSONRPCRequest):
    method: Literal["tasks/send"] = "tasks/send"
    params: TaskSendParams


class SendTaskResponse(JSONRPCResponse):
    result: Optional[Task] = None


class SendTaskStreamingRequest(JSONRPCRequest):
    method: Literal["tasks/sendSubscribe"] = "tasks/sendSubscribe"
    params: TaskSendParams


class SendTaskStreamingResponse(JSONRPCResponse):
    # The result field will contain one of the event types
    result: Optional[Union[TaskStatusUpdateEvent, TaskArtifactUpdateEvent]] = None


class GetTaskRequest(JSONRPCRequest):
    method: Literal["tasks/get"] = "tasks/get"
    params: TaskQueryParams


class GetTaskResponse(JSONRPCResponse):
    result: Optional[Task] = None


class CancelTaskRequest(JSONRPCRequest):
    method: Literal["tasks/cancel"] = "tasks/cancel"
    params: TaskIdParams


class CancelTaskResponse(JSONRPCResponse):
    result: Optional[Task] = None


class SetTaskPushNotificationRequest(JSONRPCRequest):
    method: Literal["tasks/pushNotification/set"] = "tasks/pushNotification/set"
    params: TaskPushNotificationConfig


class SetTaskPushNotificationResponse(JSONRPCResponse):
    result: Optional[TaskPushNotificationConfig] = None


class GetTaskPushNotificationRequest(JSONRPCRequest):
    method: Literal["tasks/pushNotification/get"] = "tasks/pushNotification/get"
    params: TaskIdParams


class GetTaskPushNotificationResponse(JSONRPCResponse):
    result: Optional[TaskPushNotificationConfig] = None


class TaskResubscriptionRequest(JSONRPCRequest):
    method: Literal["tasks/resubscribe"] = "tasks/resubscribe"
    params: TaskIdParams  # Resubscribing might need query params later, but ID is minimal


# --- Knowledge Graph Collaboration Types ---

class KGSubject(BaseModel):
    id: str = Field(description="URI or unique identifier for the subject.")
    type: Optional[str] = Field(None, description="Optional URI representing the type of the subject.")  # format: uri


class KGPredicate(BaseModel):
    id: str = Field(description="URI representing the type of the predicate/relationship.")  # format: uri


class KGObject(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "description": "Represents the object of a Knowledge Graph statement, which can be another node (resource) or a literal value. Enforces that either 'id' or 'value' must be present, but not both."
        }
    )
    id: Optional[str] = Field(None, description="URI or unique identifier if the object is a resource/node.")  # format: uri
    value: Optional[Any] = Field(None, description="The literal value if the object is an attribute (e.g., string, number, boolean).")
    type: Optional[str] = Field(None,
                                description="Optional URI representing the type of the object node (if 'id' is present) or the literal datatype (if 'value' is present, e.g., xsd:string, xsd:integer).")  # format: uri

    @model_validator(mode="after")
    def check_content(self) -> Self:
        if self.id is None and self.value is None:
            raise ValueError("KGObject must have either 'id' or 'value'")
        if self.id is not None and self.value is not None:
            raise ValueError("KGObject cannot have both 'id' and 'value'")
        return self


class KGStatement(BaseModel):
    subject: KGSubject
    predicate: KGPredicate
    object: KGObject
    graph: Optional[str] = Field(None, description="Optional named graph URI this statement belongs to.")  # format: uri
    certainty: Optional[float] = Field(None, ge=0.0, le=1.0, description="Optional certainty score (0.0 to 1.0) associated with this statement.")
    provenance: Optional[Dict[str, Any]] = Field(None,
                                                 description="Optional metadata about the source or origin of this statement (e.g., source agent ID, timestamp).")


class PatchOperationType(str, Enum):
    ADD = "add"
    REMOVE = "remove"
    REPLACE = "replace"  # Note: Semantics might require clarification/specific handling


class KnowledgeGraphPatch(BaseModel):
    op: PatchOperationType
    statement: KGStatement


class KnowledgeQueryParams(BaseModel):
    query: str = Field(description="The query string (e.g., GraphQL query).")
    queryLanguage: Literal["graphql"] = Field("graphql", description="Specifies the language of the query.")
    variables: Optional[Dict[str, Any]] = Field(None, description="Optional dictionary of variables for the query (common in GraphQL).")
    taskId: Optional[str] = Field(None, description="Optional ID linking this query to a specific task.")
    sessionId: Optional[str] = Field(None, description="Optional ID linking this query to a specific session.")
    requiredCertainty: Optional[float] = Field(None, ge=0.0, le=1.0, description="Optional minimum certainty score for results.")
    maxAgeSeconds: Optional[int] = Field(None, ge=0, description="Optional maximum age (in seconds) for the data considered.")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata, potentially including authentication tokens or alignment context.")


class KnowledgeUpdateParams(BaseModel):
    mutations: List[KnowledgeGraphPatch] = Field(description="A list of patch operations to apply to the knowledge graph.")
    taskId: Optional[str] = Field(None, description="Optional ID linking this update to a specific task.")
    sessionId: Optional[str] = Field(None, description="Optional ID linking this update to a specific session.")
    sourceAgentId: Optional[str] = Field(None, description="Optional identifier of the agent proposing the update.")
    justification: Optional[str] = Field(None, description="Optional textual justification for the proposed update.")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata, potentially including authentication tokens or alignment context.")


class KnowledgeSubscribeParams(BaseModel):
    subscriptionQuery: str = Field(description="The query string for the subscription (e.g., GraphQL subscription).")
    queryLanguage: Literal["graphql"] = Field("graphql", description="Specifies the language of the subscription query.")
    variables: Optional[Dict[str, Any]] = Field(None, description="Optional dictionary of variables for the subscription query.")
    taskId: Optional[str] = Field(None, description="Optional ID linking this subscription to a specific task.")
    sessionId: Optional[str] = Field(None, description="Optional ID linking this subscription to a specific session.")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata, potentially including authentication tokens or alignment context.")


class KnowledgeQueryRequest(JSONRPCRequest):
    method: Literal["knowledge/query"] = "knowledge/query"
    params: KnowledgeQueryParams


class KnowledgeUpdateRequest(JSONRPCRequest):
    method: Literal["knowledge/update"] = "knowledge/update"
    params: KnowledgeUpdateParams


class KnowledgeSubscribeRequest(JSONRPCRequest):
    method: Literal["knowledge/subscribe"] = "knowledge/subscribe"
    params: KnowledgeSubscribeParams


class KnowledgeQueryResponseResult(BaseModel):
    data: Optional[Union[Dict[str, Any], List[Any]]] = Field(None,
                                                             description="The result data from the query execution, typically matching the structure requested in the GraphQL query.")
    queryMetadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata about the query execution (e.g., sources consulted, execution time).")


class KnowledgeQueryResponse(JSONRPCResponse):
    result: Optional[KnowledgeQueryResponseResult] = None


class KnowledgeUpdateResponseResult(BaseModel):
    success: bool = Field(description="Indicates if the update operation was accepted and applied (at least provisionally).")
    statementsAffected: Optional[int] = Field(None, ge=0, description="Optional count of how many statements were added or removed.")
    affectedIds: Optional[List[str]] = Field(None, description="Optional list of URIs or identifiers of entities created or modified by the update.")
    verificationStatus: Optional[str] = Field(None, description="Optional status regarding the verification of the update against alignment rules (CO-FORM).",
                                              examples=["Verified", "Pending Review", "Rejected - Constraint Violation"])
    verificationDetails: Optional[str] = Field(None, description="Optional details explaining the verification status.")


class KnowledgeUpdateResponse(JSONRPCResponse):
    result: Optional[KnowledgeUpdateResponseResult] = None


class KnowledgeGraphChangeEvent(BaseModel):
    op: PatchOperationType
    statement: KGStatement
    changeId: str = Field(default_factory=lambda: uuid4().hex, description="Unique identifier for this specific change event.")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp when the change was confirmed (ISO 8601 format).")
    changeMetadata: Optional[Dict[str, Any]] = Field(None,
                                                     description="Optional metadata about the confirmed change (e.g., who verified it, relation to a task).")

    @field_serializer("timestamp")
    def serialize_dt(self, dt: datetime, _info):
        return dt.isoformat()


class KnowledgeSubscriptionEvent(JSONRPCResponse):
    # This wraps the change event for streaming via SSE
    # The JSONRPCResponse 'id' should match the original KnowledgeSubscribeRequest ID
    result: Optional[KnowledgeGraphChangeEvent] = None


# --- Union Type for All Requests ---

A2ARequest = TypeAdapter(
    Annotated[
        Union[
            # Task methods
            SendTaskRequest,
            GetTaskRequest,
            CancelTaskRequest,
            SetTaskPushNotificationRequest,
            GetTaskPushNotificationRequest,
            TaskResubscriptionRequest,
            SendTaskStreamingRequest,
                # Knowledge methods
            KnowledgeQueryRequest,
            KnowledgeUpdateRequest,
            KnowledgeSubscribeRequest,
        ],
        Field(discriminator="method", description="Represents any valid A2A request message."),
    ]
)


# --- Error Types ---

class JSONParseError(JSONRPCError):
    code: int = -32700
    message: str = "Invalid JSON payload"


class InvalidRequestError(JSONRPCError):
    code: int = -32600
    message: str = "Request payload validation error"


class MethodNotFoundError(JSONRPCError):
    code: int = -32601
    message: str = "Method not found"


class InvalidParamsError(JSONRPCError):
    code: int = -32602
    message: str = "Invalid parameters"


class InternalError(JSONRPCError):
    code: int = -32603
    message: str = "Internal error"


class TaskNotFoundError(JSONRPCError):
    code: int = -32001
    message: str = "Task not found"


class TaskNotCancelableError(JSONRPCError):
    code: int = -32002
    message: str = "Task cannot be canceled"


class PushNotificationNotSupportedError(JSONRPCError):
    code: int = -32003
    message: str = "Push Notification is not supported"


class UnsupportedOperationError(JSONRPCError):
    code: int = -32004
    message: str = "This operation is not supported"


class ContentTypeNotSupportedError(JSONRPCError):
    code: int = -32005
    message: str = "Incompatible content types"


# New Knowledge Graph Error Types
class KnowledgeQueryError(JSONRPCError):
    code: int = -32010
    message: str = "Knowledge query failed"


class KnowledgeUpdateError(JSONRPCError):
    code: int = -32011
    message: str = "Knowledge update failed (e.g., conflict, constraint violation)"


class KnowledgeSubscriptionError(JSONRPCError):
    code: int = -32012
    message: str = "Knowledge subscription failed"


class AlignmentViolationError(JSONRPCError):
    code: int = -32013
    message: str = "Operation violates alignment constraints"


# --- Agent Card Structure ---

class AgentProvider(BaseModel):
    organization: str
    url: Optional[str] = None


class AgentCapabilities(BaseModel):
    streaming: bool = Field(False, description="Indicates if the agent supports streaming responses (e.g., tasks/sendSubscribe, knowledge/subscribe).")
    pushNotifications: bool = Field(False, description="Indicates if the agent supports server-sent push notifications for task updates.")
    stateTransitionHistory: bool = Field(False, description="Indicates if the agent tracks and provides task state transition history.")
    # New KG Capabilities
    knowledgeGraph: bool = Field(False,
                                 description="Indicates if the agent supports the knowledge graph collaboration methods (knowledge/query, knowledge/update, knowledge/subscribe).")
    knowledgeGraphQueryLanguages: List[str] = Field(default_factory=list,
                                                    description="List of query languages supported for knowledge graph interactions (e.g., 'graphql', 'sparql').")


class AgentAuthentication(BaseModel):
    schemes: List[str]
    credentials: Optional[str] = None


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
    url: str = Field(description="The endpoint URL for the agent's A2A service.")
    provider: Optional[AgentProvider] = None
    version: str
    documentationUrl: Optional[str] = None
    capabilities: AgentCapabilities
    authentication: Optional[AgentAuthentication] = None
    defaultInputModes: List[str] = Field(default=["text"])
    defaultOutputModes: List[str] = Field(default=["text"])
    skills: List[AgentSkill]


# --- Client Specific Exception Types ---

class A2AClientError(Exception):
    """Base class for A2A client-side errors."""
    pass


class A2AClientHTTPError(A2AClientError):
    """Represents an HTTP error during communication with the agent."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP Error {status_code}: {message}")


class A2AClientJSONError(A2AClientError):
    """Represents an error decoding JSON from the agent response."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(f"JSON Error: {message}")


# --- Other Potential Errors ---

class MissingAPIKeyError(Exception):
    """Exception for missing API key (if used by a specific agent implementation)."""
    pass