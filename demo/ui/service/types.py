from typing import Union, Any
from pydantic import BaseModel, Field, TypeAdapter
from typing import Literal, List, Annotated, Tuple
from pydantic import model_validator, ConfigDict, field_serializer
from uuid import uuid4
from enum import Enum
from typing_extensions import Self

from common.types import Message, Task, TaskStatus, Artifact, JSONRPCMessage, JSONRPCRequest, JSONRPCError, JSONRPCResponse, AgentCard


class Conversation(BaseModel):
  conversation_id: str
  is_active: bool
  name: str = ''
  task_ids: list[str] = Field(default_factory=list)
  messages: list[Message] = Field(default_factory=list)

class Event(BaseModel):
  id: str
  actor: str = ""
  # TODO: Extend to support internal concepts for models, like function calls.
  content: Message
  timestamp: float

class SendMessageRequest(JSONRPCRequest):
  method: Literal["message/send"] = "message/send"
  params: Message

class ListMessageRequest(JSONRPCRequest):
  method: Literal["message/list"] = "message/list"
  # This is the conversation id
  params: str

class ListMessageResponse(JSONRPCResponse):
  result: list[Message] | None = None

class MessageInfo(BaseModel):
  message_id: str
  conversation_id: str

class SendMessageResponse(JSONRPCResponse):
  result: Message | MessageInfo | None = None

class GetEventRequest(JSONRPCRequest):
  method: Literal["events/get"] = "events/get"

class GetEventResponse(JSONRPCResponse):
  result: list[Event] | None = None

class ListConversationRequest(JSONRPCRequest):
  method: Literal["conversation/list"] = "conversation/list"

class ListConversationResponse(JSONRPCResponse):
  result: list[Conversation] | None = None

class PendingMessageRequest(JSONRPCRequest):
  method: Literal["message/pending"] = "message/pending"

class PendingMessageResponse(JSONRPCResponse):
  result: list[Tuple[str, str]] | None = None

class CreateConversationRequest(JSONRPCRequest):
  method: Literal["conversation/create"] = "conversation/create"

class CreateConversationResponse(JSONRPCResponse):
  result: Conversation | None = None

class ListTaskRequest(JSONRPCRequest):
  method: Literal["task/list"] = "task/list"

class ListTaskResponse(JSONRPCResponse):
  result: list[Task] | None = None

class RegisterAgentRequest(JSONRPCRequest):
  method: Literal["agent/register"] = "agent/register"
  # This is the base url of the agent card
  params: str | None = None

class RegisterAgentResponse(JSONRPCResponse):
  result: str | None = None

class ListAgentRequest(JSONRPCRequest):
  method: Literal["agent/list"] = "agent/list"

class ListAgentResponse(JSONRPCResponse):
  result: list[AgentCard] | None = None

AgentRequest = TypeAdapter(
    Annotated[
        Union[
            SendMessageRequest,
            ListConversationRequest,
        ],
        Field(discriminator="method"),
    ]
)

class AgentClientError(Exception):
    pass

class AgentClientHTTPError(AgentClientError):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP Error {status_code}: {message}")

class AgentClientJSONError(AgentClientError):
    def __init__(self, message: str):
        self.message = message
        super().__init__(f"JSON Error: {message}")
