# test_schema.py
import pytest
import json
from uuid import uuid4
from datetime import datetime
from pathlib import Path

# import types from a2a package
from common.types import (
    TaskState, TextPart, FileContent, FilePart, DataPart, Message, TaskStatus,
    Artifact, Task, TaskStatusUpdateEvent, TaskArtifactUpdateEvent, AuthenticationInfo,
    PushNotificationConfig, TaskIdParams, TaskQueryParams, TaskSendParams, TaskPushNotificationConfig,
    JSONRPCError, SendTaskRequest, SendTaskStreamingResponse,SendTaskResponse,
    GetTaskRequest, GetTaskResponse, CancelTaskRequest, CancelTaskResponse,
    SetTaskPushNotificationRequest,
    SetTaskPushNotificationResponse, GetTaskPushNotificationRequest, GetTaskPushNotificationResponse,
    TaskResubscriptionRequest, A2ARequest, # A2ARequest is a TypeAdapter
    JSONParseError, InvalidRequestError, MethodNotFoundError, InvalidParamsError,
    InternalError, TaskNotFoundError, TaskNotCancelableError,
    PushNotificationNotSupportedError, UnsupportedOperationError,
    AgentProvider, AgentCapabilities, AgentAuthentication, AgentSkill, AgentCard
)

from jsonschema import validate, Draft7Validator, RefResolver, ValidationError

# Path to the specification
SCHEMA_FILE = Path(__file__).parent.parent / "specification/json/a2a.json"

@pytest.fixture(scope="module")
def schema():
    """Provides the loaded JSON schema from schema.json."""
    if not SCHEMA_FILE.is_file():
        pytest.fail(f"Schema file not found at {SCHEMA_FILE.resolve()}")
    try:
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Error decoding JSON from {SCHEMA_FILE.resolve()}: {e}")
    except Exception as e:
        pytest.fail(f"Error reading schema file {SCHEMA_FILE.resolve()}: {e}")


@pytest.fixture(scope="module")
def resolver(schema):
    """Provides a resolver for the loaded schema."""
    return RefResolver.from_schema(schema)

# --- Helper Functions ---

def validate_instance(instance_data, definition_name, schema, resolver):
    """Helper function to validate instance data against a specific definition."""
    definition_schema = schema["$defs"].get(definition_name)
    assert definition_schema is not None, f"Definition {definition_name} not found in schema"

    try:
        # Validate the instance against its specific definition, providing the resolver
        validate(instance=instance_data, schema=definition_schema, resolver=resolver, format_checker=Draft7Validator.FORMAT_CHECKER)
    except ValidationError as e:
        # Use pytest.fail for better error reporting in pytest
        pytest.fail(f"Validation failed for {definition_name} with data:\n{json.dumps(instance_data, indent=2)}\nSchema Path: {e.schema_path}\nInstance Path: {e.path}\nValidator: {e.validator} = {e.validator_value}\nError: {e.message}")
    except Exception as e:
         pytest.fail(f"Unexpected error during validation for {definition_name}:\n{json.dumps(instance_data, indent=2)}\nError: {e}")



# --- Basic Types ---
def test_text_part(schema, resolver):
    instance = TextPart(text="Hello world", metadata={"source": "user"})
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "TextPart", schema, resolver)
    instance_minimal = TextPart(text="Minimal")
    validate_instance(instance_minimal.model_dump(mode='json', exclude_none=True), "TextPart", schema, resolver)

def test_file_content(schema, resolver):
    instance_bytes = FileContent(name="test.bin", mimeType="application/octet-stream", bytes="YWFh") # "aaa" in base64
    validate_instance(instance_bytes.model_dump(mode='json', exclude_none=True), "FileContent", schema, resolver)
    instance_uri = FileContent(name="test.txt", uri="file:///tmp/test.txt")
    validate_instance(instance_uri.model_dump(mode='json', exclude_none=True), "FileContent", schema, resolver)

def test_file_part(schema, resolver):
    file_content = FileContent(uri="data:text/plain;base64,SGVsbG8sIFdvcmxkIQ==")
    instance = FilePart(file=file_content, metadata={"encoding": "base64"})
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "FilePart", schema, resolver)

def test_data_part(schema, resolver):
    instance = DataPart(data={"key": "value", "number": 123, "bool": True}, metadata={"origin": "system"})
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "DataPart", schema, resolver)

# --- Composite Types ---
def test_message(schema, resolver):
    text_part = TextPart(text="Query")
    file_part = FilePart(file=FileContent(bytes="YWFh"))
    data_part = DataPart(data={"param": 1})
    instance_user = Message(role="user", parts=[text_part])
    validate_instance(instance_user.model_dump(mode='json', exclude_none=True), "Message", schema, resolver)

    instance_agent = Message(
        role="agent",
        parts=[text_part, file_part, data_part],
        metadata={"timestamp": datetime.now().isoformat()}
    )
    dumped_agent_msg = instance_agent.model_dump(mode='json', exclude_none=True)
    validate_instance(dumped_agent_msg, "Message", schema, resolver)
    # Ensure parts were serialized correctly within the message
    assert dumped_agent_msg["parts"][0]["type"] == "text"
    assert dumped_agent_msg["parts"][1]["type"] == "file"
    assert dumped_agent_msg["parts"][2]["type"] == "data"

def test_task_status(schema, resolver):
    ts = datetime.now()
    instance = TaskStatus(state=TaskState.WORKING, message=Message(role="agent", parts=[TextPart(text="Processing...")]))
    dumped_data = instance.model_dump(mode='json', exclude_none=True)
    assert "timestamp" in dumped_data
    validate_instance(dumped_data, "TaskStatus", schema, resolver)

    instance_completed = TaskStatus(state=TaskState.COMPLETED, timestamp=ts)
    dumped_completed = instance_completed.model_dump(mode='json', exclude_none=True)
    assert dumped_completed["timestamp"] == ts.isoformat() # Check serializer
    validate_instance(dumped_completed, "TaskStatus", schema, resolver)

def test_artifact(schema, resolver):
    instance = Artifact(
        name="result.txt",
        description="Final output",
        parts=[TextPart(text="Done")],
        metadata={"generated_by": "processor"}
    )
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "Artifact", schema, resolver)
    instance_minimal = Artifact(parts=[DataPart(data={"status": "ok"})])
    validate_instance(instance_minimal.model_dump(mode='json', exclude_none=True), "Artifact", schema, resolver)
    instance_chunk = Artifact(parts=[DataPart(data={"status": "ok"})], index=1, lastChunk=False, append=True)
    validate_instance(instance_chunk.model_dump(mode='json', exclude_none=True), "Artifact", schema, resolver)

def test_task(schema, resolver):
    status = TaskStatus(state=TaskState.COMPLETED)
    artifact = Artifact(parts=[TextPart(text="Result")])
    instance = Task(
        id=uuid4().hex,
        sessionId=uuid4().hex,
        status=status,
        artifacts=[artifact],
        metadata={"user_id": 123}
    )
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "Task", schema, resolver)
    instance_minimal = Task(id=uuid4().hex, status=TaskStatus(state=TaskState.SUBMITTED))
    validate_instance(instance_minimal.model_dump(mode='json', exclude_none=True), "Task", schema, resolver)

def test_task_status_update_event(schema, resolver):
    status = TaskStatus(state=TaskState.WORKING)
    instance = TaskStatusUpdateEvent(
        id=uuid4().hex,
        status=status,
        final=False,
        metadata={"update_seq": 1}
    )
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "TaskStatusUpdateEvent", schema, resolver)
    instance_final = TaskStatusUpdateEvent(id=uuid4().hex, status=TaskStatus(state=TaskState.FAILED), final=True)
    validate_instance(instance_final.model_dump(mode='json', exclude_none=True), "TaskStatusUpdateEvent", schema, resolver)

def test_task_artifact_update_event(schema, resolver):
    artifact =Artifact(
        name="result.txt",
        description="Final output",
        parts=[TextPart(text="Done")],
        metadata={"generated_by": "processor"}
    )
    instance = TaskArtifactUpdateEvent(
        id=uuid4().hex,
        artifact=artifact,
        final=False,
        metadata={"update_seq": 1}
    )
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "TaskArtifactUpdateEvent", schema, resolver)
    instance_final = TaskArtifactUpdateEvent(id=uuid4().hex, artifact=artifact, final=True)
    validate_instance(instance_final.model_dump(mode='json', exclude_none=True), "TaskArtifactUpdateEvent", schema, resolver)

# --- Configuration/Params ---
def test_authentication_info(schema, resolver):
    instance = AuthenticationInfo(schemes=["bearer"], credentials="token123")
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "AuthenticationInfo", schema, resolver)
    # Test extra fields allowed by schema (additionalProperties: {})
    instance_extra = AuthenticationInfo(schemes=["basic"], extra_field="some_value")
    validate_instance(instance_extra.model_dump(mode='json', exclude_none=True), "AuthenticationInfo", schema, resolver)

def test_push_notification_config(schema, resolver):
    auth = AuthenticationInfo(schemes=["bearer"], credentials="abc")
    instance = PushNotificationConfig(url="https://example.com/callback", token="secret", authentication=auth)
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "PushNotificationConfig", schema, resolver)
    instance_no_auth = PushNotificationConfig(url="http://localhost/notify", token="simple")
    validate_instance(instance_no_auth.model_dump(mode='json', exclude_none=True), "PushNotificationConfig", schema, resolver)

def test_task_query_params(schema, resolver):
    instance = TaskQueryParams(id=uuid4().hex, metadata={"filter": "active"})
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "TaskQueryParams", schema, resolver)
    instance = TaskQueryParams(id=uuid4().hex, historyLength=2, metadata={"filter": "active"})
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "TaskQueryParams", schema, resolver)
    instance_minimal = TaskQueryParams(id=uuid4().hex)
    validate_instance(instance_minimal.model_dump(mode='json', exclude_none=True), "TaskQueryParams", schema, resolver)

def test_task_id_params(schema, resolver):
    instance = TaskIdParams(id=uuid4().hex, metadata={"filter": "active"})
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "TaskIdParams", schema, resolver)
    instance_minimal = TaskIdParams(id=uuid4().hex)
    validate_instance(instance_minimal.model_dump(mode='json', exclude_none=True), "TaskIdParams", schema, resolver)

def test_task_send_params(schema, resolver):
    msg = Message(role="user", parts=[TextPart(text="Start processing")])
    pushNotificationConfig = PushNotificationConfig(url="http://...", token="tok")
    instance = TaskSendParams(
        id=uuid4().hex,
        sessionId=uuid4().hex, # Explicit session ID
        message=msg,
        stream=True,
        pushNotification=pushNotificationConfig,
        metadata={"priority": 1}
    )
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "TaskSendParams", schema, resolver)

    # Test with default session ID
    instance_default_session = TaskSendParams(id=uuid4().hex, message=msg)
    dumped_data = instance_default_session.model_dump(mode='json', exclude_none=True)
    assert isinstance(dumped_data.get("sessionId"), str) # Check factory worked
    validate_instance(dumped_data, "TaskSendParams", schema, resolver)

def test_task_push_notification_config(schema, resolver):
    pushNotificationConfig = PushNotificationConfig(url="http://...", token="tok")
    instance = TaskPushNotificationConfig(id=uuid4().hex, pushNotificationConfig=pushNotificationConfig)
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "TaskPushNotificationConfig", schema, resolver)

# --- RPC Specific Messages ---

def test_jsonrpc_error(schema, resolver):
    instance = JSONRPCError(code=-32000, message="Server error", data={"details": "trace..."})
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "JSONRPCError", schema, resolver)
    instance_minimal = JSONRPCError(code=1, message="Custom")
    validate_instance(instance_minimal.model_dump(mode='json', exclude_none=True), "JSONRPCError", schema, resolver)

# Use parametrize for testing multiple error types cleanly
@pytest.mark.parametrize("error_cls", [
    JSONParseError, InvalidRequestError, MethodNotFoundError,
    InvalidParamsError, InternalError, TaskNotFoundError,
    TaskNotCancelableError, PushNotificationNotSupportedError,
    UnsupportedOperationError
])
def test_specific_errors(error_cls, schema, resolver):
    instance = error_cls() # Use defaults
    validate_instance(instance.model_dump(mode='json', exclude_none=True), error_cls.__name__, schema, resolver)

    # Add data if allowed (not const null) and test again
    if 'data' in error_cls.model_fields and error_cls.model_fields['data'].annotation is not type(None):
         instance_with_data = error_cls(data={"info": "more"})
         validate_instance(instance_with_data.model_dump(mode='json', exclude_none=True), error_cls.__name__, schema, resolver)


def test_send_task_request(schema, resolver):
    params = TaskSendParams(id="t1", message=Message(role="user", parts=[TextPart(text="go")]))
    instance = SendTaskRequest(params=params, id=1) # Use default method and jsonrpc
    dumped_data = instance.model_dump(mode='json', exclude_none=True)
    assert dumped_data["method"] == "tasks/send"
    validate_instance(dumped_data, "SendTaskRequest", schema, resolver)

def test_send_task_response(schema, resolver):
    # Result case 1: Task
    task_result = Task(id="t1", status=TaskStatus(state=TaskState.SUBMITTED))
    instance_task = SendTaskResponse(id=1, result=task_result)
    validate_instance(instance_task.model_dump(mode='json', exclude_none=True), "SendTaskResponse", schema, resolver)

    # Result case 2: TaskStatusUpdateEvent
    update_result = TaskStatusUpdateEvent(id="t1", status=TaskStatus(state=TaskState.WORKING))
    instance_update = SendTaskStreamingResponse(id=1, result=update_result)
    validate_instance(instance_update.model_dump(mode='json', exclude_none=True), "SendTaskStreamingResponse", schema, resolver)

    # Error case
    error = TaskNotFoundError()
    instance_error = SendTaskStreamingResponse(id=1, error=error)
    validate_instance(instance_error.model_dump(mode='json', exclude_none=True), "SendTaskStreamingResponse", schema, resolver)

    artifact = Artifact(name="result.txt", parts=[TextPart(text="Done")])
    task_artifact_update_event = TaskArtifactUpdateEvent(id="t1", artifact=artifact)
    response_event = SendTaskStreamingResponse(id=1, result=task_artifact_update_event)
    validate_instance(response_event.model_dump(mode='json', exclude_none=True), "SendTaskStreamingResponse", schema, resolver)
    

def test_get_task_request(schema, resolver):
    params = TaskQueryParams(id="t1")
    instance = GetTaskRequest(params=params, id=2)
    dumped_data = instance.model_dump(mode='json', exclude_none=True)
    assert dumped_data["method"] == "tasks/get"
    validate_instance(dumped_data, "GetTaskRequest", schema, resolver)

def test_get_task_response(schema, resolver):
    task_result = Task(id="t1", status=TaskStatus(state=TaskState.COMPLETED))
    instance = GetTaskResponse(id=2, result=task_result)
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "GetTaskResponse", schema, resolver)

    error = TaskNotFoundError()
    instance_error = GetTaskResponse(id=2, error=error)
    validate_instance(instance_error.model_dump(mode='json', exclude_none=True), "GetTaskResponse", schema, resolver)

def test_cancel_task_request(schema, resolver):
    params = TaskIdParams(id="t1")
    instance = CancelTaskRequest(params=params, id=3)
    dumped_data = instance.model_dump(mode='json', exclude_none=True)
    assert dumped_data["method"] == "tasks/cancel"
    validate_instance(dumped_data, "CancelTaskRequest", schema, resolver)

def test_cancel_task_response(schema, resolver):
    task_result = Task(id="t1", status=TaskStatus(state=TaskState.CANCELED))
    instance = CancelTaskResponse(id=3, result=task_result)
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "CancelTaskResponse", schema, resolver)

    error = TaskNotCancelableError()
    instance_error = CancelTaskResponse(id=3, error=error)
    validate_instance(instance_error.model_dump(mode='json', exclude_none=True), "CancelTaskResponse", schema, resolver)

def test_set_task_push_notification_request(schema, resolver):
    params = TaskPushNotificationConfig(id="t1", pushNotificationConfig=PushNotificationConfig(url="http://...", token="t"))
    instance = SetTaskPushNotificationRequest(params=params, id=5)
    dumped_data = instance.model_dump(mode='json', exclude_none=True)
    assert dumped_data["method"] == "tasks/pushNotification/set"
    validate_instance(dumped_data, "SetTaskPushNotificationRequest", schema, resolver)

def test_set_task_push_notification_response(schema, resolver):
    cb_info = TaskPushNotificationConfig(id="t1", pushNotificationConfig=PushNotificationConfig(url="http://...", token="t"))
    instance = SetTaskPushNotificationResponse(id=5, result=cb_info)
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "SetTaskPushNotificationResponse", schema, resolver)

    error = PushNotificationNotSupportedError()
    instance_error = SetTaskPushNotificationResponse(id=5, error=error)
    validate_instance(instance_error.model_dump(mode='json', exclude_none=True), "SetTaskPushNotificationResponse", schema, resolver)

def test_get_task_push_notification_request(schema, resolver):
    params = TaskIdParams(id="t1")
    instance = GetTaskPushNotificationRequest(params=params, id=6)
    dumped_data = instance.model_dump(mode='json', exclude_none=True)
    assert dumped_data["method"] == "tasks/pushNotification/get"
    validate_instance(dumped_data, "GetTaskPushNotificationRequest", schema, resolver)

def test_get_task_push_notification_response(schema, resolver):
    cb_info = TaskPushNotificationConfig(id="t1", pushNotificationConfig=PushNotificationConfig(url="http://...", token="t"))
    instance = GetTaskPushNotificationResponse(id=6, result=cb_info)
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "GetTaskPushNotificationResponse", schema, resolver)

    # Case where push notifications might not be set (result=null)
    instance_null = GetTaskPushNotificationResponse(id=6, result=None)
    validate_instance(instance_null.model_dump(mode='json', exclude_none=True), "GetTaskPushNotificationResponse", schema, resolver)

    error = TaskNotFoundError()
    instance_error = GetTaskPushNotificationResponse(id=6, error=error)
    validate_instance(instance_error.model_dump(mode='json', exclude_none=True), "GetTaskPushNotificationResponse", schema, resolver)

def test_task_subscription_request(schema, resolver):
    params = TaskIdParams(id="t1")
    instance = TaskResubscriptionRequest(params=params, id=7)
    dumped_data = instance.model_dump(mode='json', exclude_none=True)
    assert dumped_data["method"] == "tasks/resubscribe"
    validate_instance(dumped_data, "TaskResubscriptionRequest", schema, resolver)

# --- A2ARequest Union ---
# Use parametrize for testing multiple request types against the union schema
@pytest.mark.parametrize("request_instance", [
    SendTaskRequest(params=TaskSendParams(id="t1", message=Message(role="user", parts=[TextPart(text="go")]))),
    GetTaskRequest(params=TaskQueryParams(id="t2")),
    CancelTaskRequest(params=TaskIdParams(id="t3")),
    SetTaskPushNotificationRequest(params=TaskPushNotificationConfig(id="t5", pushNotificationConfig=PushNotificationConfig(url="http://..", token="."))),
    GetTaskPushNotificationRequest(params=TaskIdParams(id="t6")),
    TaskResubscriptionRequest(params=TaskIdParams(id="t7"))
])
def test_a2a_request_union(request_instance, schema, resolver):
    # The A2ARequest definition itself uses oneOf and discriminator
    a2a_schema_ref = {"$ref": "#/$defs/A2ARequest"}
    instance_data = A2ARequest.dump_python(request_instance, mode='json', exclude_none=True)

    try:
        # Validate directly against the A2ARequest definition reference
        validate(instance=instance_data, schema=a2a_schema_ref, resolver=resolver, format_checker=Draft7Validator.FORMAT_CHECKER)
    except ValidationError as e:
        pytest.fail(f"Validation failed for A2ARequest ({request_instance.method}) with data:\n{json.dumps(instance_data, indent=2)}\nSchema Path: {e.schema_path}\nInstance Path: {e.path}\nValidator: {e.validator} = {e.validator_value}\nError: {e.message}")
    except Exception as e:
        pytest.fail(f"Unexpected error during A2ARequest validation ({request_instance.method}):\n{json.dumps(instance_data, indent=2)}\nError: {e}")

# --- Agent Info ---
def test_agent_provider(schema, resolver):
    instance = AgentProvider(organization="TestOrg", url="https://test.org")
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "AgentProvider", schema, resolver)
    instance_min = AgentProvider(organization="MinOrg")
    validate_instance(instance_min.model_dump(mode='json', exclude_none=True), "AgentProvider", schema, resolver)

def test_agent_capabilities(schema, resolver):
    instance = AgentCapabilities(streaming=True, pushNotifications=False, stateTransitionHistory=True)
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "AgentCapabilities", schema, resolver)
    instance_default = AgentCapabilities()
    validate_instance(instance_default.model_dump(mode='json', exclude_none=True), "AgentCapabilities", schema, resolver)

def test_agent_authentication(schema, resolver):
    instance = AgentAuthentication(schemes=["api_key"], credentials=None)
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "AgentAuthentication", schema, resolver)

def test_agent_skill(schema, resolver):
    instance = AgentSkill(
        id="summarize",
        name="Text Summarization",
        description="Summarizes long text",
        tags=["nlp", "text"],
        examples=["Summarize this document...", "Give me the key points of:"],
        inputModes=["text", "file"],
        outputModes=["text"]
    )
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "AgentSkill", schema, resolver)
    instance_minimal = AgentSkill(id="echo", name="Echo Skill")
    validate_instance(instance_minimal.model_dump(mode='json', exclude_none=True), "AgentSkill", schema, resolver)

def test_agent_card(schema, resolver):
    provider = AgentProvider(organization="AI Inc.")
    caps = AgentCapabilities(streaming=True)
    auth = AgentAuthentication(schemes=["bearer"])
    skill = AgentSkill(id="translate", name="Translation")
    instance = AgentCard(
        name="Multilingual Agent",
        description="Translates text between languages.",
        url="https://agent.example.com",
        provider=provider,
        version="1.2.0",
        documentationUrl="https://agent.example.com/docs",
        capabilities=caps,
        authentication=auth,
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        skills=[skill]
    )
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "AgentCard", schema, resolver)

    instance_minimal = AgentCard(
        name="Simple Agent",
        version="0.1",
        url="https://agent.example.com",
        capabilities=AgentCapabilities(), # Use defaults
        skills=[AgentSkill(id="ping", name="Ping")]
    )
    validate_instance(instance_minimal.model_dump(mode='json', exclude_none=True), "AgentCard", schema, resolver)
