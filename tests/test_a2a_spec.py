# test_schema.py
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest
from jsonschema import validate, Draft7Validator, RefResolver, ValidationError

# import types from a2a package
# TODO Don't want to sound too "pydantic" here, but would it not be better to use the full paths as per PEP8?
from A2A.samples.python.common.types import (
    # Core Task Types
    TaskState, TextPart, FileContent, FilePart, DataPart, Message, TaskStatus,
    Artifact, Task, TaskStatusUpdateEvent, TaskArtifactUpdateEvent, AuthenticationInfo,
    PushNotificationConfig, TaskIdParams, TaskQueryParams, TaskSendParams, TaskPushNotificationConfig,
    # Base RPC Types
    JSONRPCError,  # Added base types for clarity
    # Task Requests/Responses
    SendTaskRequest, SendTaskStreamingRequest, SendTaskResponse, SendTaskStreamingResponse,
    GetTaskRequest, GetTaskResponse, CancelTaskRequest, CancelTaskResponse,
    SetTaskPushNotificationRequest,
    SetTaskPushNotificationResponse, GetTaskPushNotificationRequest, GetTaskPushNotificationResponse,
    TaskResubscriptionRequest,
    # Knowledge Graph Types (NEW)
    KGSubject, KGPredicate, KGObject, KGStatement, PatchOperationType, KnowledgeGraphPatch,
    KnowledgeQueryParams, KnowledgeUpdateParams, KnowledgeSubscribeParams,
    KnowledgeQueryRequest, KnowledgeUpdateRequest, KnowledgeSubscribeRequest,
    KnowledgeQueryResponseResult, KnowledgeUpdateResponseResult,
    KnowledgeQueryResponse, KnowledgeUpdateResponse,
    KnowledgeGraphChangeEvent, KnowledgeSubscriptionEvent,
    # Union Request Type
    A2ARequest,  # A2ARequest is a TypeAdapter
    # Error Types
    JSONParseError, InvalidRequestError, MethodNotFoundError, InvalidParamsError,
    InternalError, TaskNotFoundError, TaskNotCancelableError,
    PushNotificationNotSupportedError, UnsupportedOperationError, ContentTypeNotSupportedError,  # Added ContentType...
    # New KG Error Types
    KnowledgeQueryError, KnowledgeUpdateError, KnowledgeSubscriptionError, AlignmentViolationError,
    # Agent Card Types
    AgentProvider, AgentCapabilities, AgentAuthentication, AgentSkill, AgentCard
)

# Path to the specification (ADJUST IF YOUR PATH IS DIFFERENT)
SPEC_DIR = Path(__file__).parent.parent / "specification/json"
SCHEMA_FILE = SPEC_DIR / "a2a.json"


@pytest.fixture(scope="module")
def schema():
    """Provides the loaded JSON schema from a2a.json."""
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
    base_uri = SCHEMA_FILE.resolve().as_uri()
    return RefResolver(base_uri=base_uri, referrer=schema)


# --- Helper Functions ---

def validate_instance(instance_data, definition_name, schema, resolver):
    """Helper function to validate instance data against a specific definition."""
    definition_schema = schema["$defs"].get(definition_name)
    assert definition_schema is not None, f"Definition '{definition_name}' not found in schema $defs"

    try:
        validate(instance=instance_data, schema=definition_schema, resolver=resolver, format_checker=Draft7Validator.FORMAT_CHECKER)
    except ValidationError as e:
        pytest.fail(
            f"Validation failed for '{definition_name}' with data:\n{json.dumps(instance_data, indent=2)}\n"
            f"Schema Path: {list(e.schema_path)}\nInstance Path: {list(e.path)}\n"
            f"Validator: {e.validator} = {e.validator_value}\nError: {e.message}")
    except Exception as e:
        pytest.fail(f"Unexpected error during validation for '{definition_name}':\n{json.dumps(instance_data, indent=2)}\nError: {e}")


# --- Test Functions (Organized by Type) ---

# --- Basic Types ---
def test_text_part(schema, resolver):
    instance = TextPart(text="Hello world", metadata={"source": "user"})
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "TextPart", schema, resolver)
    instance_minimal = TextPart(text="Minimal")
    validate_instance(instance_minimal.model_dump(mode='json', exclude_none=True), "TextPart", schema, resolver)


def test_file_content(schema, resolver):
    instance_bytes = FileContent(name="test.bin", mimeType="application/octet-stream", bytes="YWFh")  # "aaa" in base64
    validate_instance(instance_bytes.model_dump(mode='json', exclude_none=True), "FileContent", schema, resolver)
    instance_uri = FileContent(name="test.txt", uri="file:///tmp/test.txt", mimeType="text/plain")
    validate_instance(instance_uri.model_dump(mode='json', exclude_none=True), "FileContent", schema, resolver)
    instance_min_uri = FileContent(uri="http://example.com/data")
    validate_instance(instance_min_uri.model_dump(mode='json', exclude_none=True), "FileContent", schema, resolver)


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
    assert dumped_agent_msg["parts"][0]["type"] == "text"
    assert dumped_agent_msg["parts"][1]["type"] == "file"
    assert dumped_agent_msg["parts"][2]["type"] == "data"


def test_task_status(schema, resolver):
    ts = datetime.now()
    msg = Message(role="agent", parts=[TextPart(text="Processing...")])
    instance = TaskStatus(state=TaskState.WORKING, message=msg, timestamp=ts)
    dumped_data = instance.model_dump(mode='json', exclude_none=True)
    assert "timestamp" in dumped_data
    assert dumped_data["timestamp"] == ts.isoformat()  # Check serializer
    validate_instance(dumped_data, "TaskStatus", schema, resolver)

    instance_completed = TaskStatus(state=TaskState.COMPLETED)  # Use default timestamp
    dumped_completed = instance_completed.model_dump(mode='json', exclude_none=True)
    assert "timestamp" in dumped_completed
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
    instance_chunk = Artifact(parts=[DataPart(data={"chunk": "..."})], index=1, lastChunk=False, append=True)
    validate_instance(instance_chunk.model_dump(mode='json', exclude_none=True), "Artifact", schema, resolver)


def test_task(schema, resolver):
    status = TaskStatus(state=TaskState.COMPLETED)
    artifact = Artifact(parts=[TextPart(text="Result")])
    msg_hist = [Message(role="user", parts=[TextPart(text="Start")]), Message(role="agent", parts=[TextPart(text="OK")])]
    instance = Task(
        id=uuid4().hex,
        sessionId=uuid4().hex,
        status=status,
        artifacts=[artifact],
        history=msg_hist,
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
    artifact = Artifact(name="log.txt", parts=[TextPart(text="...")])
    instance = TaskArtifactUpdateEvent(
        id=uuid4().hex,
        artifact=artifact,
        metadata={"update_type": "log_chunk"}
    )
    # Note: TaskArtifactUpdateEvent in types.py had 'final' field which isn't in schema, removed it from test
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "TaskArtifactUpdateEvent", schema, resolver)


# --- Configuration/Params ---
def test_authentication_info(schema, resolver):
    instance = AuthenticationInfo(schemes=["bearer"], credentials="token123")
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "AuthenticationInfo", schema, resolver)
    instance_extra = AuthenticationInfo(schemes=["basic"], extra_field="some_value")
    validate_instance(instance_extra.model_dump(mode='json', exclude_none=True), "AuthenticationInfo", schema, resolver)


def test_push_notification_config(schema, resolver):
    auth = AuthenticationInfo(schemes=["bearer"], credentials="abc")
    instance = PushNotificationConfig(url="https://example.com/callback", token="secret", authentication=auth)
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "PushNotificationConfig", schema, resolver)
    instance_no_auth = PushNotificationConfig(url="http://localhost/notify", token="simple")
    validate_instance(instance_no_auth.model_dump(mode='json', exclude_none=True), "PushNotificationConfig", schema, resolver)


def test_task_id_params(schema, resolver):
    instance = TaskIdParams(id=uuid4().hex, metadata={"filter": "active"})
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "TaskIdParams", schema, resolver)
    instance_minimal = TaskIdParams(id=uuid4().hex)
    validate_instance(instance_minimal.model_dump(mode='json', exclude_none=True), "TaskIdParams", schema, resolver)


def test_task_query_params(schema, resolver):
    instance = TaskQueryParams(id=uuid4().hex, metadata={"requester": "agent_x"})
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "TaskQueryParams", schema, resolver)
    instance_hist = TaskQueryParams(id=uuid4().hex, historyLength=10)
    validate_instance(instance_hist.model_dump(mode='json', exclude_none=True), "TaskQueryParams", schema, resolver)
    instance_hist_zero = TaskQueryParams(id=uuid4().hex, historyLength=0)
    validate_instance(instance_hist_zero.model_dump(mode='json', exclude_none=True), "TaskQueryParams", schema, resolver)
    instance_minimal = TaskQueryParams(id=uuid4().hex)
    validate_instance(instance_minimal.model_dump(mode='json', exclude_none=True), "TaskQueryParams", schema, resolver)


def test_task_send_params(schema, resolver):
    msg = Message(role="user", parts=[TextPart(text="Start processing")])
    push_config = PushNotificationConfig(url="http://example.com/notify", token="tok")
    instance = TaskSendParams(
        id=uuid4().hex,
        sessionId=uuid4().hex,
        message=msg,
        acceptedOutputModes=["text/plain", "image/png"],
        pushNotification=push_config,
        historyLength=5,
        metadata={"priority": 1}
    )
    # Note: Removed 'stream=True' as it's not part of TaskSendParams
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "TaskSendParams", schema, resolver)

    instance_default_session = TaskSendParams(id=uuid4().hex, message=msg)
    dumped_data = instance_default_session.model_dump(mode='json', exclude_none=True)
    assert isinstance(dumped_data.get("sessionId"), str)
    validate_instance(dumped_data, "TaskSendParams", schema, resolver)


def test_task_push_notification_config(schema, resolver):
    push_config = PushNotificationConfig(url="http://example.com/webhook")
    instance = TaskPushNotificationConfig(id=uuid4().hex, pushNotificationConfig=push_config)
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "TaskPushNotificationConfig", schema, resolver)


# --- RPC Specific Messages ---

def test_jsonrpc_error(schema, resolver):
    instance = JSONRPCError(code=-32000, message="Server error", data={"details": "trace..."})
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "JSONRPCError", schema, resolver)
    instance_minimal = JSONRPCError(code=1, message="Custom")
    validate_instance(instance_minimal.model_dump(mode='json', exclude_none=True), "JSONRPCError", schema, resolver)


# Use parametrize for testing multiple error types cleanly
@pytest.mark.parametrize("error_cls, def_name", [
    # Errors where data is Optional[Any] or allows non-null values
    (JSONParseError, "JSONParseError"),
    (InvalidRequestError, "InvalidRequestError"),
    (InvalidParamsError, "InvalidParamsError"),
    (InternalError, "InternalError"),
    (KnowledgeQueryError, "KnowledgeQueryError"),
    (KnowledgeUpdateError, "KnowledgeUpdateError"),
    (KnowledgeSubscriptionError, "KnowledgeSubscriptionError"),
    (AlignmentViolationError, "AlignmentViolationError"),
    # Errors where data MUST be null according to schema
    (MethodNotFoundError, "MethodNotFoundError"),
    (TaskNotFoundError, "TaskNotFoundError"),
    (TaskNotCancelableError, "TaskNotCancelableError"),
    (PushNotificationNotSupportedError, "PushNotificationNotSupportedError"),
    (UnsupportedOperationError, "UnsupportedOperationError"),
    (ContentTypeNotSupportedError, "ContentTypeNotSupportedError"),
])
def test_specific_errors(error_cls, def_name, schema, resolver):
    # Define which errors require data: null
    requires_null_data = def_name in [
        "MethodNotFoundError", "TaskNotFoundError", "TaskNotCancelableError",
        "PushNotificationNotSupportedError", "UnsupportedOperationError",
        "ContentTypeNotSupportedError"
    ]

    # Instantiate: Always include data=None if required by schema
    # The types.py fix ensures data=None is handled correctly now
    instance = error_cls(data=None)

    # Dump the instance: Use exclude_none=False ONLY for types requiring data:null
    if requires_null_data:
        # *** THE FIX: Don't exclude none for these specific errors ***
        instance_data = instance.model_dump(mode='json', exclude_none=False)
        # Ensure 'data' is actually present and null
        assert 'data' in instance_data and instance_data['data'] is None, \
            f"{def_name} dump missing required 'data': null field. Dumped: {instance_data}"
    else:
        # For other errors, exclude_none=True is fine (data is truly optional or can hold values)
        instance_data = instance.model_dump(mode='json', exclude_none=True)
        # Ensure 'data' is NOT present if it was None
        assert 'data' not in instance_data, \
            f"{def_name} dump included 'data': null when it should be omitted. Dumped: {instance_data}"

    # Validate against schema
    validate_instance(instance_data, def_name, schema, resolver)

    # Test with non-null data if allowed by the model definition
    if not requires_null_data:
        try:
            # data field inherited from JSONRPCError is Optional[Any]
            instance_with_data = error_cls(data={"info": "more"})
            instance_data_with_data = instance_with_data.model_dump(mode='json', exclude_none=True)
            # 'data' should be present here
            assert 'data' in instance_data_with_data and instance_data_with_data['data'] == {"info": "more"}, \
                f"{def_name} dump failed to include non-null data. Dumped: {instance_data_with_data}"
            validate_instance(instance_data_with_data, def_name, schema, resolver)
        except Exception as e:
            pytest.fail(f"Failed to validate {def_name} with data: {e}")


# --- Remaining tests (should mostly be okay, check for exclude_none usage) ---

def test_send_task_request(schema, resolver):
    params = TaskSendParams(id="t1", message=Message(role="user", parts=[TextPart(text="go")]))
    instance = SendTaskRequest(params=params, id=1)
    dumped_data = instance.model_dump(mode='json', exclude_none=True)
    assert dumped_data["method"] == "tasks/send"
    validate_instance(dumped_data, "SendTaskRequest", schema, resolver)


def test_send_task_response(schema, resolver):
    task_result = Task(id="t1", status=TaskStatus(state=TaskState.SUBMITTED))
    instance_task = SendTaskResponse(id=1, result=task_result)
    validate_instance(instance_task.model_dump(mode='json', exclude_none=True), "SendTaskResponse", schema, resolver)

    error = TaskNotFoundError(data=None)  # Explicitly set data=None
    instance_error = SendTaskResponse(id=1, error=error)
    # Use exclude_none=False because TaskNotFoundError requires data:null
    dumped_error = instance_error.model_dump(mode='json', exclude_none=False)
    assert 'data' in dumped_error['error'] and dumped_error['error']['data'] is None
    validate_instance(dumped_error, "SendTaskResponse", schema, resolver)


def test_send_task_streaming_response(schema, resolver):
    update_result = TaskStatusUpdateEvent(id="t1", status=TaskStatus(state=TaskState.WORKING))
    instance_update = SendTaskStreamingResponse(id=1, result=update_result)
    validate_instance(instance_update.model_dump(mode='json', exclude_none=True), "SendTaskStreamingResponse", schema, resolver)

    artifact = Artifact(name="output.png", parts=[FilePart(file=FileContent(bytes="aaaa"))])
    artifact_event = TaskArtifactUpdateEvent(id="t1", artifact=artifact)
    instance_artifact = SendTaskStreamingResponse(id=1, result=artifact_event)
    validate_instance(instance_artifact.model_dump(mode='json', exclude_none=True), "SendTaskStreamingResponse", schema, resolver)

    error = InternalError(data={"details": "stream error"})  # Error that allows data
    instance_error = SendTaskStreamingResponse(id=1, error=error)
    validate_instance(instance_error.model_dump(mode='json', exclude_none=True), "SendTaskStreamingResponse", schema, resolver)

    error_null_data = TaskNotFoundError(data=None)  # Error requiring data:null
    instance_error_null = SendTaskStreamingResponse(id=1, error=error_null_data)
    dumped_error_null = instance_error_null.model_dump(mode='json', exclude_none=False)  # Use exclude_none=False
    assert 'data' in dumped_error_null['error'] and dumped_error_null['error']['data'] is None
    validate_instance(dumped_error_null, "SendTaskStreamingResponse", schema, resolver)


# ... (rest of the tests should be similar, adjust model_dump call for specific errors) ...

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

    error = TaskNotFoundError(data=None)  # Requires data:null
    instance_error = GetTaskResponse(id=2, error=error)
    dumped_error = instance_error.model_dump(mode='json', exclude_none=False)  # Use exclude_none=False
    assert 'data' in dumped_error['error'] and dumped_error['error']['data'] is None
    validate_instance(dumped_error, "GetTaskResponse", schema, resolver)


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

    error = TaskNotCancelableError(data=None)  # Requires data:null
    instance_error = CancelTaskResponse(id=3, error=error)
    dumped_error = instance_error.model_dump(mode='json', exclude_none=False)  # Use exclude_none=False
    assert 'data' in dumped_error['error'] and dumped_error['error']['data'] is None
    validate_instance(dumped_error, "CancelTaskResponse", schema, resolver)


def test_set_task_push_notification_request(schema, resolver):
    params = TaskPushNotificationConfig(id="t1", pushNotificationConfig=PushNotificationConfig(url="http://notify.me"))
    instance = SetTaskPushNotificationRequest(params=params, id=5)
    dumped_data = instance.model_dump(mode='json', exclude_none=True)
    assert dumped_data["method"] == "tasks/pushNotification/set"
    validate_instance(dumped_data, "SetTaskPushNotificationRequest", schema, resolver)


def test_set_task_push_notification_response(schema, resolver):
    cb_info = TaskPushNotificationConfig(id="t1", pushNotificationConfig=PushNotificationConfig(url="http://notify.me"))
    instance = SetTaskPushNotificationResponse(id=5, result=cb_info)
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "SetTaskPushNotificationResponse", schema, resolver)

    error = PushNotificationNotSupportedError(data=None)  # Requires data:null
    instance_error = SetTaskPushNotificationResponse(id=5, error=error)
    dumped_error = instance_error.model_dump(mode='json', exclude_none=False)  # Use exclude_none=False
    assert 'data' in dumped_error['error'] and dumped_error['error']['data'] is None
    validate_instance(dumped_error, "SetTaskPushNotificationResponse", schema, resolver)


def test_get_task_push_notification_request(schema, resolver):
    params = TaskIdParams(id="t1")
    instance = GetTaskPushNotificationRequest(params=params, id=6)
    dumped_data = instance.model_dump(mode='json', exclude_none=True)
    assert dumped_data["method"] == "tasks/pushNotification/get"
    validate_instance(dumped_data, "GetTaskPushNotificationRequest", schema, resolver)


def test_get_task_push_notification_response(schema, resolver):
    cb_info = TaskPushNotificationConfig(id="t1", pushNotificationConfig=PushNotificationConfig(url="http://notify.me"))
    instance = GetTaskPushNotificationResponse(id=6, result=cb_info)
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "GetTaskPushNotificationResponse", schema, resolver)

    instance_null = GetTaskPushNotificationResponse(id=6, result=None)
    validate_instance(instance_null.model_dump(mode='json', exclude_none=True), "GetTaskPushNotificationResponse", schema, resolver)

    error = TaskNotFoundError(data=None)  # Requires data:null
    instance_error = GetTaskPushNotificationResponse(id=6, error=error)
    dumped_error = instance_error.model_dump(mode='json', exclude_none=False)  # Use exclude_none=False
    assert 'data' in dumped_error['error'] and dumped_error['error']['data'] is None
    validate_instance(dumped_error, "GetTaskPushNotificationResponse", schema, resolver)


def test_task_resubscription_request(schema, resolver):
    params = TaskIdParams(id="t1")
    instance = TaskResubscriptionRequest(params=params, id=7)
    dumped_data = instance.model_dump(mode='json', exclude_none=True)
    assert dumped_data["method"] == "tasks/resubscribe"
    validate_instance(dumped_data, "TaskResubscriptionRequest", schema, resolver)


# --- Knowledge Graph Types (NEW TESTS - OK) ---
# These tests should be fine as they don't involve the problematic errors

def test_kg_subject(schema, resolver):
    instance = KGSubject(id="http://example.org/entity/e1", type="http://example.org/ontology#Person")
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "KGSubject", schema, resolver)
    instance_minimal = KGSubject(id="ex:e2")
    validate_instance(instance_minimal.model_dump(mode='json', exclude_none=True), "KGSubject", schema, resolver)


def test_kg_predicate(schema, resolver):
    instance = KGPredicate(id="http://example.org/ontology#hasName")
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "KGPredicate", schema, resolver)


def test_kg_object(schema, resolver):
    instance_resource = KGObject(id="http://example.org/entity/e2", type="http://example.org/ontology#Location")
    validate_instance(instance_resource.model_dump(mode='json', exclude_none=True), "KGObject", schema, resolver)
    instance_literal_str = KGObject(value="Example Name", type="http://www.w3.org/2001/XMLSchema#string")
    validate_instance(instance_literal_str.model_dump(mode='json', exclude_none=True), "KGObject", schema, resolver)
    instance_literal_int = KGObject(value=123)
    validate_instance(instance_literal_int.model_dump(mode='json', exclude_none=True), "KGObject", schema, resolver)
    instance_min_res = KGObject(id="ex:e3")
    validate_instance(instance_min_res.model_dump(mode='json', exclude_none=True), "KGObject", schema, resolver)
    instance_min_lit = KGObject(value=True)
    validate_instance(instance_min_lit.model_dump(mode='json', exclude_none=True), "KGObject", schema, resolver)


def test_kg_statement(schema, resolver):
    subj = KGSubject(id="ex:e1")
    pred = KGPredicate(id="ex:prop1")
    obj = KGObject(value="Some Value")
    instance = KGStatement(
        subject=subj,
        predicate=pred,
        object=obj,
        graph="ex:graph1",
        certainty=0.9,
        provenance={"source": "agent_y"}
    )
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "KGStatement", schema, resolver)
    instance_minimal = KGStatement(subject=subj, predicate=pred, object=KGObject(id="ex:e2"))
    validate_instance(instance_minimal.model_dump(mode='json', exclude_none=True), "KGStatement", schema, resolver)


def test_knowledge_graph_patch(schema, resolver):
    stmt = KGStatement(
        subject=KGSubject(id="ex:s"),
        predicate=KGPredicate(id="ex:p"),
        object=KGObject(value=1)
    )
    instance_add = KnowledgeGraphPatch(op=PatchOperationType.ADD, statement=stmt)
    validate_instance(instance_add.model_dump(mode='json', exclude_none=True), "KnowledgeGraphPatch", schema, resolver)
    instance_remove = KnowledgeGraphPatch(op=PatchOperationType.REMOVE, statement=stmt)
    validate_instance(instance_remove.model_dump(mode='json', exclude_none=True), "KnowledgeGraphPatch", schema, resolver)


def test_knowledge_query_params(schema, resolver):
    instance = KnowledgeQueryParams(
        query="{ find(id: \"123\") { name } }",
        queryLanguage="graphql",
        variables={"id": "123"},
        taskId="task-abc",
        sessionId="sess-xyz",
        requiredCertainty=0.8,
        maxAgeSeconds=3600,
        metadata={"auth": "token"}
    )
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "KnowledgeQueryParams", schema, resolver)
    instance_minimal = KnowledgeQueryParams(query="{ me { id } }")
    validate_instance(instance_minimal.model_dump(mode='json', exclude_none=True), "KnowledgeQueryParams", schema, resolver)


def test_knowledge_update_params(schema, resolver):
    patch1 = KnowledgeGraphPatch(op="add", statement=KGStatement(subject=KGSubject(id="ex:s"), predicate=KGPredicate(id="ex:p"), object=KGObject(id="ex:o")))
    patch2 = KnowledgeGraphPatch(op="remove",
                                 statement=KGStatement(subject=KGSubject(id="ex:s"), predicate=KGPredicate(id="ex:q"), object=KGObject(value="old")))
    instance = KnowledgeUpdateParams(
        mutations=[patch1, patch2],
        taskId="task-1",
        sessionId="sess-1",
        sourceAgentId="agent_updater",
        justification="Updating based on new observation.",
        metadata={"tx_id": "tx123"}
    )
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "KnowledgeUpdateParams", schema, resolver)
    instance_minimal = KnowledgeUpdateParams(mutations=[patch1])
    validate_instance(instance_minimal.model_dump(mode='json', exclude_none=True), "KnowledgeUpdateParams", schema, resolver)


def test_knowledge_subscribe_params(schema, resolver):
    instance = KnowledgeSubscribeParams(
        subscriptionQuery="subscription { onEvent { id data } }",
        queryLanguage="graphql",
        variables={"topic": "updates"},
        taskId="task-sub",
        sessionId="sess-sub",
        metadata={"filter": "critical"}
    )
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "KnowledgeSubscribeParams", schema, resolver)
    instance_minimal = KnowledgeSubscribeParams(subscriptionQuery="subscription { onPing }")
    validate_instance(instance_minimal.model_dump(mode='json', exclude_none=True), "KnowledgeSubscribeParams", schema, resolver)


# --- KG RPC Messages (OK) ---

def test_knowledge_query_request(schema, resolver):
    params = KnowledgeQueryParams(query="{ me { id } }")
    instance = KnowledgeQueryRequest(params=params, id="kq1")
    dumped_data = instance.model_dump(mode='json', exclude_none=True)
    assert dumped_data["method"] == "knowledge/query"
    validate_instance(dumped_data, "KnowledgeQueryRequest", schema, resolver)


def test_knowledge_update_request(schema, resolver):
    patch = KnowledgeGraphPatch(op="add", statement=KGStatement(subject=KGSubject(id="ex:s"), predicate=KGPredicate(id="ex:p"), object=KGObject(id="ex:o")))
    params = KnowledgeUpdateParams(mutations=[patch])
    instance = KnowledgeUpdateRequest(params=params, id="ku1")
    dumped_data = instance.model_dump(mode='json', exclude_none=True)
    assert dumped_data["method"] == "knowledge/update"
    validate_instance(dumped_data, "KnowledgeUpdateRequest", schema, resolver)


def test_knowledge_subscribe_request(schema, resolver):
    params = KnowledgeSubscribeParams(subscriptionQuery="subscription { onPing }")
    instance = KnowledgeSubscribeRequest(params=params, id="ks1")
    dumped_data = instance.model_dump(mode='json', exclude_none=True)
    assert dumped_data["method"] == "knowledge/subscribe"
    validate_instance(dumped_data, "KnowledgeSubscribeRequest", schema, resolver)


def test_knowledge_query_response(schema, resolver):
    result = KnowledgeQueryResponseResult(
        data={"me": {"id": "agent-b", "name": "Bob"}},
        queryMetadata={"source_cache_hit": True}
    )
    instance_success = KnowledgeQueryResponse(id="kq1", result=result)
    validate_instance(instance_success.model_dump(mode='json', exclude_none=True), "KnowledgeQueryResponse", schema, resolver)
    result_null = KnowledgeQueryResponseResult(data=None)
    instance_null = KnowledgeQueryResponse(id="kq2", result=result_null)
    validate_instance(instance_null.model_dump(mode='json', exclude_none=True), "KnowledgeQueryResponse", schema, resolver)

    instance_error = KnowledgeQueryResponse(id="kq3", error=KnowledgeQueryError(data={"details": "Syntax error"}))  # Allows data
    validate_instance(instance_error.model_dump(mode='json', exclude_none=True), "KnowledgeQueryResponse", schema, resolver)


def test_knowledge_update_response(schema, resolver):
    result = KnowledgeUpdateResponseResult(
        success=True,
        statementsAffected=2,
        affectedIds=["ex:s", "ex:o"],
        verificationStatus="Verified"
    )
    instance_success = KnowledgeUpdateResponse(id="ku1", result=result)
    validate_instance(instance_success.model_dump(mode='json', exclude_none=True), "KnowledgeUpdateResponse", schema, resolver)
    result_fail = KnowledgeUpdateResponseResult(
        success=False,
        verificationStatus="Rejected - Constraint Violation",
        verificationDetails="Statement conflicts with existing fact and policy P12"
    )
    instance_fail = KnowledgeUpdateResponse(id="ku2", result=result_fail)
    validate_instance(instance_fail.model_dump(mode='json', exclude_none=True), "KnowledgeUpdateResponse", schema, resolver)

    instance_error = KnowledgeUpdateResponse(id="ku3", error=AlignmentViolationError(data={"constraint_id": "C001"}))  # Allows data
    validate_instance(instance_error.model_dump(mode='json', exclude_none=True), "KnowledgeUpdateResponse", schema, resolver)


def test_knowledge_graph_change_event(schema, resolver):
    ts = datetime.now()
    stmt = KGStatement(subject=KGSubject(id="ex:s"), predicate=KGPredicate(id="ex:p"), object=KGObject(value=True))
    instance = KnowledgeGraphChangeEvent(
        op=PatchOperationType.ADD,
        statement=stmt,
        changeId=uuid4().hex,
        timestamp=ts,
        changeMetadata={"verified_by": "agent_b"}
    )
    dumped_data = instance.model_dump(mode='json', exclude_none=True)
    assert dumped_data["timestamp"] == ts.isoformat()
    validate_instance(dumped_data, "KnowledgeGraphChangeEvent", schema, resolver)


def test_knowledge_subscription_event(schema, resolver):
    # Success case (contains change event)
    change = KnowledgeGraphChangeEvent(
        op=PatchOperationType.REMOVE,
        statement=KGStatement(subject=KGSubject(id="ex:s"), predicate=KGPredicate(id="ex:p"), object=KGObject(id="ex:o"))
    )
    instance_success = KnowledgeSubscriptionEvent(id="ks1", result=change)
    validate_instance(instance_success.model_dump(mode='json', exclude_none=True), "KnowledgeSubscriptionEvent", schema, resolver)

    # Error case (streamed error)
    # FIX: Wrap the error data string in an object to match schema { type: object } or { type: null }
    error_data_obj = {"details": "Stream disconnected"}
    instance_error = KnowledgeSubscriptionEvent(id="ks1", error=KnowledgeSubscriptionError(data=error_data_obj))
    # Use exclude_none=True because KnowledgeSubscriptionError allows non-null data, and we are providing it.
    validate_instance(instance_error.model_dump(mode='json', exclude_none=True), "KnowledgeSubscriptionEvent", schema, resolver)


# --- A2ARequest Union (OK) ---
@pytest.mark.parametrize("request_instance", [
    SendTaskRequest(params=TaskSendParams(id="t1", message=Message(role="user", parts=[TextPart(text="go")]))),
    GetTaskRequest(params=TaskQueryParams(id="t2")),
    CancelTaskRequest(params=TaskIdParams(id="t3")),
    SetTaskPushNotificationRequest(params=TaskPushNotificationConfig(id="t5", pushNotificationConfig=PushNotificationConfig(url="http://.."))),
    GetTaskPushNotificationRequest(params=TaskIdParams(id="t6")),
    TaskResubscriptionRequest(params=TaskIdParams(id="t7")),
    SendTaskStreamingRequest(params=TaskSendParams(id="t8", message=Message(role="user", parts=[TextPart(text="stream")]))),
    KnowledgeQueryRequest(params=KnowledgeQueryParams(query="{ping}")),
    KnowledgeUpdateRequest(params=KnowledgeUpdateParams(
        mutations=[KnowledgeGraphPatch(op="add", statement=KGStatement(subject=KGSubject(id="s"), predicate=KGPredicate(id="p"), object=KGObject(value=1)))])),
    KnowledgeSubscribeRequest(params=KnowledgeSubscribeParams(subscriptionQuery="sub { evt }")),
])
def test_a2a_request_union(request_instance, schema, resolver):
    a2a_schema_ref = {"$ref": "#/$defs/A2ARequest"}
    instance_data = A2ARequest.dump_python(request_instance, mode='json', exclude_none=True)
    try:
        validate(instance=instance_data, schema=a2a_schema_ref, resolver=resolver, format_checker=Draft7Validator.FORMAT_CHECKER)
    except ValidationError as e:
        pytest.fail(
            f"Validation failed for A2ARequest ({request_instance.method}) with data:\n{json.dumps(instance_data, indent=2)}\n"
            f"Schema Path: {list(e.schema_path)}\nInstance Path: {list(e.path)}\n"
            f"Validator: {e.validator} = {e.validator_value}\nError: {e.message}")
    except Exception as e:
        pytest.fail(f"Unexpected error during A2ARequest validation ({request_instance.method}):\n{json.dumps(instance_data, indent=2)}\nError: {e}")


# --- Agent Info (OK) ---
def test_agent_provider(schema, resolver):
    instance = AgentProvider(organization="TestOrg", url="https://test.org")
    validate_instance(instance.model_dump(mode='json', exclude_none=True), "AgentProvider", schema, resolver)
    instance_min = AgentProvider(organization="MinOrg")
    validate_instance(instance_min.model_dump(mode='json', exclude_none=True), "AgentProvider", schema, resolver)


def test_agent_capabilities(schema, resolver):
    instance_kg = AgentCapabilities(
        streaming=True,
        pushNotifications=False,
        stateTransitionHistory=True,
        knowledgeGraph=True,
        knowledgeGraphQueryLanguages=["graphql"]
    )
    validate_instance(instance_kg.model_dump(mode='json', exclude_none=True), "AgentCapabilities", schema, resolver)
    instance_default = AgentCapabilities()
    dumped_default = instance_default.model_dump(mode='json', exclude_none=True)
    assert dumped_default.get("knowledgeGraph") is False
    assert dumped_default.get("knowledgeGraphQueryLanguages") == []
    validate_instance(dumped_default, "AgentCapabilities", schema, resolver)
    instance_stream = AgentCapabilities(streaming=True)
    validate_instance(instance_stream.model_dump(mode='json', exclude_none=True), "AgentCapabilities", schema, resolver)


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
    caps = AgentCapabilities(streaming=True, knowledgeGraph=True, knowledgeGraphQueryLanguages=["graphql"])
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
        capabilities=AgentCapabilities(),
        skills=[AgentSkill(id="ping", name="Ping")]
    )
    validate_instance(instance_minimal.model_dump(mode='json', exclude_none=True), "AgentCard", schema, resolver)
