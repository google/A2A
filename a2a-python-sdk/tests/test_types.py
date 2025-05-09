from typing import Any

import pytest

from pydantic import ValidationError

from a2a.types import (
    A2AError,
    A2ARequest,
    AgentAuthentication,
    AgentCapabilities,
    AgentCard,
    AgentProvider,
    AgentSkill,
    Artifact,
    CancelTaskRequest,
    CancelTaskResponse,
    ContentTypeNotSupportedError,
    DataPart,
    FileBase,
    FilePart,
    FileWithBytes,
    FileWithUri,
    GetTaskPushNotificationConfigRequest,
    GetTaskPushNotificationConfigResponse,
    GetTaskRequest,
    GetTaskResponse,
    InternalError,
    InvalidParamsError,
    InvalidRequestError,
    JSONParseError,
    JSONRPCError,
    JSONRPCErrorResponse,
    JSONRPCMessage,
    JSONRPCRequest,
    JSONRPCResponse,
    Message,
    MethodNotFoundError,
    Part,
    PartBase,
    PushNotificationAuthenticationInfo,
    PushNotificationConfig,
    PushNotificationNotSupportedError,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageStreamingRequest,
    SendMessageStreamingResponse,
    SetTaskPushNotificationConfigRequest,
    SetTaskPushNotificationConfigResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskIdParams,
    TaskNotCancelableError,
    TaskNotFoundError,
    TaskPushNotificationConfig,
    TaskQueryParams,
    TaskResubscriptionRequest,
    MessageSendParams,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
    UnsupportedOperationError,
    GetTaskSuccessResponse,
    SendMessageStreamingSuccessResponse,
    SendMessageSuccessResponse,
    CancelTaskSuccessResponse,
    Role,
    SetTaskPushNotificationConfigSuccessResponse,
    GetTaskPushNotificationConfigSuccessResponse,
)

# --- Helper Data ---

MINIMAL_AGENT_AUTH: dict[str, Any] = {'schemes': ['Bearer']}
FULL_AGENT_AUTH: dict[str, Any] = {
    'schemes': ['Bearer', 'Basic'],
    'credentials': 'user:pass',
}

MINIMAL_AGENT_SKILL: dict[str, Any] = {
    'id': 'skill-123',
    'name': 'Recipe Finder',
    'description': 'Finds recipes',
    'tags': ['cooking'],
}
FULL_AGENT_SKILL: dict[str, Any] = {
    'id': 'skill-123',
    'name': 'Recipe Finder',
    'description': 'Finds recipes',
    'tags': ['cooking', 'food'],
    'examples': ['Find me a pasta recipe'],
    'inputModes': ['text/plain'],
    'outputModes': ['application/json'],
}

MINIMAL_AGENT_CARD: dict[str, Any] = {
    'authentication': MINIMAL_AGENT_AUTH,
    'capabilities': {},  # AgentCapabilities is required but can be empty
    'defaultInputModes': ['text/plain'],
    'defaultOutputModes': ['application/json'],
    'description': 'Test Agent',
    'name': 'TestAgent',
    'skills': [MINIMAL_AGENT_SKILL],
    'url': 'http://example.com/agent',
    'version': '1.0',
}

TEXT_PART_DATA: dict[str, Any] = {'type': 'text', 'text': 'Hello'}
FILE_URI_PART_DATA: dict[str, Any] = {
    'type': 'file',
    'file': {'uri': 'file:///path/to/file.txt', 'mimeType': 'text/plain'},
}
FILE_BYTES_PART_DATA: dict[str, Any] = {
    'type': 'file',
    'file': {'bytes': 'aGVsbG8=', 'name': 'hello.txt'},  # base64 for "hello"
}
DATA_PART_DATA: dict[str, Any] = {'type': 'data', 'data': {'key': 'value'}}

MINIMAL_MESSAGE_USER: dict[str, Any] = {
    'role': 'user',
    'parts': [TEXT_PART_DATA],
    'messageId': 'msg-123',
}

AGENT_MESSAGE_WITH_FILE: dict[str, Any] = {
    'role': 'agent',
    'parts': [TEXT_PART_DATA, FILE_URI_PART_DATA],
    'metadata': {'timestamp': 'now'},
    'messageId': 'msg-456',
}

MINIMAL_TASK_STATUS: dict[str, Any] = {'state': 'submitted'}
FULL_TASK_STATUS: dict[str, Any] = {
    'state': 'working',
    'message': MINIMAL_MESSAGE_USER,
    'timestamp': '2023-10-27T10:00:00Z',
}

MINIMAL_TASK: dict[str, Any] = {
    'id': 'task-abc',
    'contextId': 'session-xyz',
    'status': MINIMAL_TASK_STATUS,
}
FULL_TASK: dict[str, Any] = {
    'id': 'task-abc',
    'contextId': 'session-xyz',
    'status': FULL_TASK_STATUS,
    'history': [MINIMAL_MESSAGE_USER, AGENT_MESSAGE_WITH_FILE],
    'artifacts': [
        {
            'artifactId': 'artifact-123',
            'parts': [DATA_PART_DATA],
            'name': 'result_data',
        }
    ],
    'metadata': {'priority': 'high'},
}

MINIMAL_TASK_ID_PARAMS: dict[str, Any] = {'id': 'task-123'}
FULL_TASK_ID_PARAMS: dict[str, Any] = {
    'id': 'task-456',
    'metadata': {'source': 'test'},
}

JSONRPC_ERROR_DATA: dict[str, Any] = {
    'code': -32600,
    'message': 'Invalid Request',
}
JSONRPC_SUCCESS_RESULT: dict[str, Any] = {'status': 'ok', 'data': [1, 2, 3]}

# --- Test Functions ---


def test_agent_authentication_valid():
    auth = AgentAuthentication(**MINIMAL_AGENT_AUTH)
    assert auth.schemes == ['Bearer']
    assert auth.credentials is None

    auth_full = AgentAuthentication(**FULL_AGENT_AUTH)
    assert auth_full.schemes == ['Bearer', 'Basic']
    assert auth_full.credentials == 'user:pass'


def test_agent_authentication_invalid():
    with pytest.raises(ValidationError):
        AgentAuthentication(
            credentials='only_creds'
        )  # Missing schemes  # type: ignore

        AgentAuthentication(
            schemes=['Bearer'],
            extra_field='extra',  # type: ignore
        )  # Extra field


def test_agent_capabilities():
    caps = AgentCapabilities(
        streaming=None, stateTransitionHistory=None, pushNotifications=None
    )  # All optional
    assert caps.pushNotifications is None
    assert caps.stateTransitionHistory is None
    assert caps.streaming is None

    caps_full = AgentCapabilities(
        pushNotifications=True, stateTransitionHistory=False, streaming=True
    )
    assert caps_full.pushNotifications is True
    assert caps_full.stateTransitionHistory is False
    assert caps_full.streaming is True


def test_agent_provider():
    provider = AgentProvider(organization='Test Org', url='http://test.org')
    assert provider.organization == 'Test Org'
    assert provider.url == 'http://test.org'

    with pytest.raises(ValidationError):
        AgentProvider(organization='Test Org')  # Missing url  # type: ignore


def test_agent_skill_valid():
    skill = AgentSkill(**MINIMAL_AGENT_SKILL)
    assert skill.id == 'skill-123'
    assert skill.name == 'Recipe Finder'
    assert skill.description == 'Finds recipes'
    assert skill.tags == ['cooking']
    assert skill.examples is None

    skill_full = AgentSkill(**FULL_AGENT_SKILL)
    assert skill_full.examples == ['Find me a pasta recipe']
    assert skill_full.inputModes == ['text/plain']


def test_agent_skill_invalid():
    with pytest.raises(ValidationError):
        AgentSkill(
            id='abc', name='n', description='d'
        )  # Missing tags  # type: ignore

    AgentSkill(
        **MINIMAL_AGENT_SKILL,
        invalid_extra='foo',  # type: ignore
    )  # Extra field


def test_agent_card_valid():
    card = AgentCard(**MINIMAL_AGENT_CARD)
    assert card.name == 'TestAgent'
    assert card.version == '1.0'
    assert card.authentication.schemes == ['Bearer']
    assert len(card.skills) == 1
    assert card.skills[0].id == 'skill-123'
    assert card.provider is None  # Optional


def test_agent_card_invalid():
    bad_card_data = MINIMAL_AGENT_CARD.copy()
    del bad_card_data['name']
    with pytest.raises(ValidationError):
        AgentCard(**bad_card_data)  # Missing name


# --- Test Parts ---


def test_text_part():
    part = TextPart(**TEXT_PART_DATA)
    assert part.type == 'text'
    assert part.text == 'Hello'
    assert part.metadata is None

    with pytest.raises(ValidationError):
        TextPart(type='text')  # Missing text # type: ignore
    with pytest.raises(ValidationError):
        TextPart(
            type='file',  # type: ignore
            text='hello',
        )  # Wrong type literal


def test_file_part_variants():
    # URI variant
    file_uri = FileWithUri(
        uri='file:///path/to/file.txt', mimeType='text/plain'
    )
    part_uri = FilePart(type='file', file=file_uri)
    assert isinstance(part_uri.file, FileWithUri)
    assert part_uri.file.uri == 'file:///path/to/file.txt'
    assert part_uri.file.mimeType == 'text/plain'
    assert not hasattr(part_uri.file, 'bytes')

    # Bytes variant
    file_bytes = FileWithBytes(bytes='aGVsbG8=', name='hello.txt')
    part_bytes = FilePart(type='file', file=file_bytes)
    assert isinstance(part_bytes.file, FileWithBytes)
    assert part_bytes.file.bytes == 'aGVsbG8='
    assert part_bytes.file.name == 'hello.txt'
    assert not hasattr(part_bytes.file, 'uri')

    # Test deserialization directly
    part_uri_deserialized = FilePart.model_validate(FILE_URI_PART_DATA)
    assert isinstance(part_uri_deserialized.file, FileWithUri)
    assert part_uri_deserialized.file.uri == 'file:///path/to/file.txt'

    part_bytes_deserialized = FilePart.model_validate(FILE_BYTES_PART_DATA)
    assert isinstance(part_bytes_deserialized.file, FileWithBytes)
    assert part_bytes_deserialized.file.bytes == 'aGVsbG8='

    # Invalid - wrong type literal
    with pytest.raises(ValidationError):
        FilePart(type='text', file=file_uri)  # type: ignore

    FilePart(**FILE_URI_PART_DATA, extra='extra')  # type: ignore


def test_data_part():
    part = DataPart(**DATA_PART_DATA)
    assert part.type == 'data'
    assert part.data == {'key': 'value'}

    with pytest.raises(ValidationError):
        DataPart(type='data')  # Missing data  # type: ignore


def test_part_root_model():
    # Test deserialization of the Union RootModel
    part_text = Part.model_validate(TEXT_PART_DATA)
    assert isinstance(part_text.root, TextPart)
    assert part_text.root.text == 'Hello'

    part_file = Part.model_validate(FILE_URI_PART_DATA)
    assert isinstance(part_file.root, FilePart)
    assert isinstance(part_file.root.file, FileWithUri)

    part_data = Part.model_validate(DATA_PART_DATA)
    assert isinstance(part_data.root, DataPart)
    assert part_data.root.data == {'key': 'value'}

    # Test serialization
    assert part_text.model_dump(exclude_none=True) == TEXT_PART_DATA
    assert part_file.model_dump(exclude_none=True) == FILE_URI_PART_DATA
    assert part_data.model_dump(exclude_none=True) == DATA_PART_DATA


# --- Test Message and Task ---


def test_message():
    msg = Message(**MINIMAL_MESSAGE_USER)
    assert msg.role == Role.user
    assert len(msg.parts) == 1
    assert isinstance(
        msg.parts[0].root, TextPart
    )  # Access root for RootModel Part
    assert msg.metadata is None

    msg_agent = Message(**AGENT_MESSAGE_WITH_FILE)
    assert msg_agent.role == Role.agent
    assert len(msg_agent.parts) == 2
    assert isinstance(msg_agent.parts[1].root, FilePart)
    assert msg_agent.metadata == {'timestamp': 'now'}

    with pytest.raises(ValidationError):
        Message(
            role='invalid_role',  # type: ignore
            parts=[TEXT_PART_DATA],  # type: ignore
        )  # Invalid enum
    with pytest.raises(ValidationError):
        Message(role=Role.user)  # Missing parts  # type: ignore


def test_task_status():
    status = TaskStatus(**MINIMAL_TASK_STATUS)
    assert status.state == TaskState.submitted
    assert status.message is None
    assert status.timestamp is None

    status_full = TaskStatus(**FULL_TASK_STATUS)
    assert status_full.state == TaskState.working
    assert isinstance(status_full.message, Message)
    assert status_full.timestamp == '2023-10-27T10:00:00Z'

    with pytest.raises(ValidationError):
        TaskStatus(state='invalid_state')  # Invalid enum  # type: ignore


def test_task():
    task = Task(**MINIMAL_TASK)
    assert task.id == 'task-abc'
    assert task.contextId == 'session-xyz'
    assert task.status.state == TaskState.submitted
    assert task.history is None
    assert task.artifacts is None
    assert task.metadata is None

    task_full = Task(**FULL_TASK)
    assert task_full.id == 'task-abc'
    assert task_full.status.state == TaskState.working
    assert task_full.history is not None and len(task_full.history) == 2
    assert isinstance(task_full.history[0], Message)
    assert task_full.artifacts is not None and len(task_full.artifacts) == 1
    assert isinstance(task_full.artifacts[0], Artifact)
    assert task_full.artifacts[0].name == 'result_data'
    assert task_full.metadata == {'priority': 'high'}

    with pytest.raises(ValidationError):
        Task(id='abc', sessionId='xyz')  # Missing status # type: ignore


# --- Test JSON-RPC Structures ---


def test_jsonrpc_error():
    err = JSONRPCError(code=-32600, message='Invalid Request')
    assert err.code == -32600
    assert err.message == 'Invalid Request'
    assert err.data is None

    err_data = JSONRPCError(
        code=-32001, message='Task not found', data={'taskId': '123'}
    )
    assert err_data.code == -32001
    assert err_data.data == {'taskId': '123'}


def test_jsonrpc_request():
    req = JSONRPCRequest(jsonrpc='2.0', method='test_method', id=1)
    assert req.jsonrpc == '2.0'
    assert req.method == 'test_method'
    assert req.id == 1
    assert req.params is None

    req_params = JSONRPCRequest(
        jsonrpc='2.0', method='add', params={'a': 1, 'b': 2}, id='req-1'
    )
    assert req_params.params == {'a': 1, 'b': 2}
    assert req_params.id == 'req-1'

    with pytest.raises(ValidationError):
        JSONRPCRequest(
            jsonrpc='1.0',  # type: ignore
            method='m',
            id=1,
        )  # Wrong version
    with pytest.raises(ValidationError):
        JSONRPCRequest(jsonrpc='2.0', id=1)  # Missing method  # type: ignore


def test_jsonrpc_error_response():
    err_obj = JSONRPCError(**JSONRPC_ERROR_DATA)
    resp = JSONRPCErrorResponse(jsonrpc='2.0', error=err_obj, id='err-1')
    assert resp.jsonrpc == '2.0'
    assert resp.id == 'err-1'
    assert resp.error.code == -32600
    assert resp.error.message == 'Invalid Request'

    with pytest.raises(ValidationError):
        JSONRPCErrorResponse(
            jsonrpc='2.0', id='err-1'
        )  # Missing error # type: ignore


def test_jsonrpc_response_root_model() -> None:
    # Success case
    success_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'result': MINIMAL_TASK,
        'id': 1,
    }
    resp_success = JSONRPCResponse.model_validate(success_data)
    assert isinstance(resp_success.root, SendMessageSuccessResponse)
    assert resp_success.root.result == Task(**MINIMAL_TASK)

    # Error case
    error_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'error': JSONRPC_ERROR_DATA,
        'id': 'err-1',
    }
    resp_error = JSONRPCResponse.model_validate(error_data)
    assert isinstance(resp_error.root, JSONRPCErrorResponse)
    assert resp_error.root.error.code == -32600
    # Note: .model_dump() might serialize the nested error model
    assert resp_error.model_dump(exclude_none=True) == error_data

    # Invalid case (neither success nor error structure)
    with pytest.raises(ValidationError):
        JSONRPCResponse.model_validate({'jsonrpc': '2.0', 'id': 1})


# --- Test Request/Response Wrappers ---


def test_send_message_request() -> None:
    params = MessageSendParams(message=Message(**MINIMAL_MESSAGE_USER))
    req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'message/send',
        'params': params.model_dump(),
        'id': 5,
    }
    req = SendMessageRequest.model_validate(req_data)
    assert req.method == 'message/send'
    assert isinstance(req.params, MessageSendParams)
    assert req.params.message.role == Role.user

    with pytest.raises(ValidationError):  # Wrong method literal
        SendMessageRequest.model_validate(
            {**req_data, 'method': 'wrong/method'}
        )


def test_send_subscribe_request() -> None:
    params = MessageSendParams(message=Message(**MINIMAL_MESSAGE_USER))
    req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'message/sendStream',
        'params': params.model_dump(),
        'id': 5,
    }
    req = SendMessageStreamingRequest.model_validate(req_data)
    assert req.method == 'message/sendStream'
    assert isinstance(req.params, MessageSendParams)
    assert req.params.message.role == Role.user

    with pytest.raises(ValidationError):  # Wrong method literal
        SendMessageStreamingRequest.model_validate(
            {**req_data, 'method': 'wrong/method'}
        )


def test_get_task_request() -> None:
    params = TaskQueryParams(id='task-1', historyLength=2)
    req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'tasks/get',
        'params': params.model_dump(),
        'id': 5,
    }
    req = GetTaskRequest.model_validate(req_data)
    assert req.method == 'tasks/get'
    assert isinstance(req.params, TaskQueryParams)
    assert req.params.id == 'task-1'
    assert req.params.historyLength == 2

    with pytest.raises(ValidationError):  # Wrong method literal
        GetTaskRequest.model_validate({**req_data, 'method': 'wrong/method'})


def test_cancel_task_request() -> None:
    params = TaskIdParams(id='task-1')
    req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'tasks/cancel',
        'params': params.model_dump(),
        'id': 5,
    }
    req = CancelTaskRequest.model_validate(req_data)
    assert req.method == 'tasks/cancel'
    assert isinstance(req.params, TaskIdParams)
    assert req.params.id == 'task-1'

    with pytest.raises(ValidationError):  # Wrong method literal
        CancelTaskRequest.model_validate({**req_data, 'method': 'wrong/method'})


def test_get_task_response() -> None:
    resp_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'result': MINIMAL_TASK,
        'id': 'resp-1',
    }
    resp = GetTaskResponse.model_validate(resp_data)
    assert resp.root.id == 'resp-1'
    assert isinstance(resp.root, GetTaskSuccessResponse)
    assert isinstance(resp.root.result, Task)
    assert resp.root.result.id == 'task-abc'

    with pytest.raises(ValidationError):  # Result is not a Task
        GetTaskResponse.model_validate(
            {'jsonrpc': '2.0', 'result': {'wrong': 'data'}, 'id': 1}
        )

    resp_data_err: dict[str, Any] = {
        'jsonrpc': '2.0',
        'error': JSONRPCError(**TaskNotFoundError().model_dump()),
        'id': 'resp-1',
    }
    resp_err = GetTaskResponse.model_validate(resp_data_err)
    assert resp_err.root.id == 'resp-1'
    assert isinstance(resp_err.root, JSONRPCErrorResponse)
    assert resp_err.root.error is not None
    assert isinstance(resp_err.root.error, JSONRPCError)


def test_send_message_response() -> None:
    resp_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'result': MINIMAL_TASK,
        'id': 'resp-1',
    }
    resp = SendMessageResponse.model_validate(resp_data)
    assert resp.root.id == 'resp-1'
    assert isinstance(resp.root, SendMessageSuccessResponse)
    assert isinstance(resp.root.result, Task)
    assert resp.root.result.id == 'task-abc'

    with pytest.raises(ValidationError):  # Result is not a Task
        SendMessageResponse.model_validate(
            {'jsonrpc': '2.0', 'result': {'wrong': 'data'}, 'id': 1}
        )

    resp_data_err: dict[str, Any] = {
        'jsonrpc': '2.0',
        'error': JSONRPCError(**TaskNotFoundError().model_dump()),
        'id': 'resp-1',
    }
    resp_err = SendMessageResponse.model_validate(resp_data_err)
    assert resp_err.root.id == 'resp-1'
    assert isinstance(resp_err.root, JSONRPCErrorResponse)
    assert resp_err.root.error is not None
    assert isinstance(resp_err.root.error, JSONRPCError)


def test_cancel_task_response() -> None:
    resp_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'result': MINIMAL_TASK,
        'id': 1,
    }
    resp = CancelTaskResponse.model_validate(resp_data)
    assert resp.root.id == 1
    assert isinstance(resp.root, CancelTaskSuccessResponse)
    assert isinstance(resp.root.result, Task)
    assert resp.root.result.id == 'task-abc'

    resp_data_err: dict[str, Any] = {
        'jsonrpc': '2.0',
        'error': JSONRPCError(**TaskNotFoundError().model_dump()),
        'id': 'resp-1',
    }
    resp_err = CancelTaskResponse.model_validate(resp_data_err)
    assert resp_err.root.id == 'resp-1'
    assert isinstance(resp_err.root, JSONRPCErrorResponse)
    assert resp_err.root.error is not None
    assert isinstance(resp_err.root.error, JSONRPCError)


def test_send_message_streaming_status_update_response() -> None:
    task_status_update_event_data: dict[str, Any] = {
        'status': MINIMAL_TASK_STATUS,
        'taskId': '1',
        'final': False,
        'type': 'status-update',
    }

    event_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'id': 1,
        'result': task_status_update_event_data,
    }
    response = SendMessageStreamingResponse.model_validate(event_data)
    assert response.root.id == 1
    assert isinstance(response.root, SendMessageStreamingSuccessResponse)
    assert isinstance(response.root.result, TaskStatusUpdateEvent)
    assert response.root.result.status.state == TaskState.submitted
    assert response.root.result.taskId == '1'
    assert not response.root.result.final

    with pytest.raises(
        ValidationError
    ):  # Result is not a TaskStatusUpdateEvent
        SendMessageStreamingResponse.model_validate(
            {'jsonrpc': '2.0', 'result': {'wrong': 'data'}, 'id': 1}
        )

    event_data = {
        'jsonrpc': '2.0',
        'id': 1,
        'result': {**task_status_update_event_data, 'final': True},
    }
    response = SendMessageStreamingResponse.model_validate(event_data)
    assert response.root.id == 1
    assert isinstance(response.root, SendMessageStreamingSuccessResponse)
    assert isinstance(response.root.result, TaskStatusUpdateEvent)
    assert response.root.result.final

    resp_data_err: dict[str, Any] = {
        'jsonrpc': '2.0',
        'error': JSONRPCError(**TaskNotFoundError().model_dump()),
        'id': 'resp-1',
    }
    resp_err = SendMessageStreamingResponse.model_validate(resp_data_err)
    assert resp_err.root.id == 'resp-1'
    assert isinstance(resp_err.root, JSONRPCErrorResponse)
    assert resp_err.root.error is not None
    assert isinstance(resp_err.root.error, JSONRPCError)


def test_send_message_streaming_artifact_update_response() -> None:
    text_part = TextPart(**TEXT_PART_DATA)
    data_part = DataPart(**DATA_PART_DATA)
    artifact = Artifact(
        artifactId='artifact-123',
        name='result_data',
        parts=[Part(root=text_part), Part(root=data_part)],
    )
    task_artifact_update_event_data: dict[str, Any] = {
        'artifact': artifact,
        'taskId': 'task_id',
        'append': False,
        'lastChunk': True,
        'type': 'artifact-update',
    }
    event_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'id': 1,
        'result': task_artifact_update_event_data,
    }
    response = SendMessageStreamingResponse.model_validate(event_data)
    assert response.root.id == 1
    assert isinstance(response.root, SendMessageStreamingSuccessResponse)
    assert isinstance(response.root.result, TaskArtifactUpdateEvent)
    assert response.root.result.artifact.artifactId == 'artifact-123'
    assert response.root.result.artifact.name == 'result_data'
    assert response.root.result.taskId == 'task_id'
    assert not response.root.result.append
    assert response.root.result.lastChunk
    assert len(response.root.result.artifact.parts) == 2
    assert isinstance(response.root.result.artifact.parts[0].root, TextPart)
    assert isinstance(response.root.result.artifact.parts[1].root, DataPart)


def test_set_task_push_notification_response() -> None:
    task_push_config = TaskPushNotificationConfig(
        taskId='t2',
        pushNotificationConfig=PushNotificationConfig(
            url='https://example.com', token='token'
        ),
    )
    resp_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'result': task_push_config.model_dump(),
        'id': 1,
    }
    resp = SetTaskPushNotificationConfigResponse.model_validate(resp_data)
    assert resp.root.id == 1
    assert isinstance(resp.root, SetTaskPushNotificationConfigSuccessResponse)
    assert isinstance(resp.root.result, TaskPushNotificationConfig)
    assert resp.root.result.taskId == 't2'
    assert resp.root.result.pushNotificationConfig.url == 'https://example.com'
    assert resp.root.result.pushNotificationConfig.token == 'token'
    assert resp.root.result.pushNotificationConfig.authentication is None

    auth_info_dict: dict[str, Any] = {
        'schemes': ['Bearer', 'Basic'],
        'credentials': 'user:pass',
    }
    task_push_config.pushNotificationConfig.authentication = (
        PushNotificationAuthenticationInfo(**auth_info_dict)
    )
    resp_data = {
        'jsonrpc': '2.0',
        'result': task_push_config.model_dump(),
        'id': 1,
    }
    resp = SetTaskPushNotificationConfigResponse.model_validate(resp_data)
    assert isinstance(resp.root, SetTaskPushNotificationConfigSuccessResponse)
    assert resp.root.result.pushNotificationConfig.authentication is not None
    assert resp.root.result.pushNotificationConfig.authentication.schemes == [
        'Bearer',
        'Basic',
    ]
    assert (
        resp.root.result.pushNotificationConfig.authentication.credentials
        == 'user:pass'
    )

    resp_data_err: dict[str, Any] = {
        'jsonrpc': '2.0',
        'error': JSONRPCError(**TaskNotFoundError().model_dump()),
        'id': 'resp-1',
    }
    resp_err = SetTaskPushNotificationConfigResponse.model_validate(
        resp_data_err
    )
    assert resp_err.root.id == 'resp-1'
    assert isinstance(resp_err.root, JSONRPCErrorResponse)
    assert resp_err.root.error is not None
    assert isinstance(resp_err.root.error, JSONRPCError)


def test_get_task_push_notification_response() -> None:
    task_push_config = TaskPushNotificationConfig(
        taskId='t2',
        pushNotificationConfig=PushNotificationConfig(
            url='https://example.com', token='token'
        ),
    )
    resp_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'result': task_push_config.model_dump(),
        'id': 1,
    }
    resp = GetTaskPushNotificationConfigResponse.model_validate(resp_data)
    assert resp.root.id == 1
    assert isinstance(resp.root, GetTaskPushNotificationConfigSuccessResponse)
    assert isinstance(resp.root.result, TaskPushNotificationConfig)
    assert resp.root.result.taskId == 't2'
    assert resp.root.result.pushNotificationConfig.url == 'https://example.com'
    assert resp.root.result.pushNotificationConfig.token == 'token'
    assert resp.root.result.pushNotificationConfig.authentication is None

    auth_info_dict: dict[str, Any] = {
        'schemes': ['Bearer', 'Basic'],
        'credentials': 'user:pass',
    }
    task_push_config.pushNotificationConfig.authentication = (
        PushNotificationAuthenticationInfo(**auth_info_dict)
    )
    resp_data = {
        'jsonrpc': '2.0',
        'result': task_push_config.model_dump(),
        'id': 1,
    }
    resp = GetTaskPushNotificationConfigResponse.model_validate(resp_data)
    assert isinstance(resp.root, GetTaskPushNotificationConfigSuccessResponse)
    assert resp.root.result.pushNotificationConfig.authentication is not None
    assert resp.root.result.pushNotificationConfig.authentication.schemes == [
        'Bearer',
        'Basic',
    ]
    assert (
        resp.root.result.pushNotificationConfig.authentication.credentials
        == 'user:pass'
    )

    resp_data_err: dict[str, Any] = {
        'jsonrpc': '2.0',
        'error': JSONRPCError(**TaskNotFoundError().model_dump()),
        'id': 'resp-1',
    }
    resp_err = GetTaskPushNotificationConfigResponse.model_validate(
        resp_data_err
    )
    assert resp_err.root.id == 'resp-1'
    assert isinstance(resp_err.root, JSONRPCErrorResponse)
    assert resp_err.root.error is not None
    assert isinstance(resp_err.root.error, JSONRPCError)


# --- Test A2ARequest Root Model ---


def test_a2a_request_root_model() -> None:
    # SendMessageRequest case
    send_params = MessageSendParams(message=Message(**MINIMAL_MESSAGE_USER))
    send_req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'message/send',
        'params': send_params.model_dump(),
        'id': 1,
    }
    a2a_req_send = A2ARequest.model_validate(send_req_data)
    assert isinstance(a2a_req_send.root, SendMessageRequest)
    assert a2a_req_send.root.method == 'message/send'

    # SendMessageStreamingRequest case
    send_subs_req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'message/sendStream',
        'params': send_params.model_dump(),
        'id': 1,
    }
    a2a_req_send_subs = A2ARequest.model_validate(send_subs_req_data)
    assert isinstance(a2a_req_send_subs.root, SendMessageStreamingRequest)
    assert a2a_req_send_subs.root.method == 'message/sendStream'

    # GetTaskRequest case
    get_params = TaskQueryParams(id='t2')
    get_req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'tasks/get',
        'params': get_params.model_dump(),
        'id': 2,
    }
    a2a_req_get = A2ARequest.model_validate(get_req_data)
    assert isinstance(a2a_req_get.root, GetTaskRequest)
    assert a2a_req_get.root.method == 'tasks/get'

    # CancelTaskRequest case
    id_params = TaskIdParams(id='t2')
    cancel_req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'tasks/cancel',
        'params': id_params.model_dump(),
        'id': 2,
    }
    a2a_req_cancel = A2ARequest.model_validate(cancel_req_data)
    assert isinstance(a2a_req_cancel.root, CancelTaskRequest)
    assert a2a_req_cancel.root.method == 'tasks/cancel'

    # SetTaskPushNotificationConfigRequest
    task_push_config = TaskPushNotificationConfig(
        taskId='t2',
        pushNotificationConfig=PushNotificationConfig(
            url='https://example.com', token='token'
        ),
    )
    set_push_notif_req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'tasks/pushNotificationConfig/set',
        'params': task_push_config.model_dump(),
        'taskId': 2,
    }
    a2a_req_set_push_req = A2ARequest.model_validate(set_push_notif_req_data)
    assert isinstance(
        a2a_req_set_push_req.root, SetTaskPushNotificationConfigRequest
    )
    assert isinstance(
        a2a_req_set_push_req.root.params, TaskPushNotificationConfig
    )
    assert (
        a2a_req_set_push_req.root.method == 'tasks/pushNotificationConfig/set'
    )

    # GetTaskPushNotificationConfigRequest
    id_params = TaskIdParams(id='t2')
    get_push_notif_req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'tasks/pushNotificationConfig/get',
        'params': id_params.model_dump(),
        'taskId': 2,
    }
    a2a_req_get_push_req = A2ARequest.model_validate(get_push_notif_req_data)
    assert isinstance(
        a2a_req_get_push_req.root, GetTaskPushNotificationConfigRequest
    )
    assert isinstance(a2a_req_get_push_req.root.params, TaskIdParams)
    assert (
        a2a_req_get_push_req.root.method == 'tasks/pushNotificationConfig/get'
    )

    # TaskResubscriptionRequest
    task_resubscribe_req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'tasks/resubscribe',
        'params': id_params.model_dump(),
        'id': 2,
    }
    a2a_req_task_resubscribe_req = A2ARequest.model_validate(
        task_resubscribe_req_data
    )
    assert isinstance(
        a2a_req_task_resubscribe_req.root, TaskResubscriptionRequest
    )
    assert isinstance(a2a_req_task_resubscribe_req.root.params, TaskIdParams)
    assert a2a_req_task_resubscribe_req.root.method == 'tasks/resubscribe'

    # Invalid method case
    invalid_req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'invalid/method',
        'params': {},
        'id': 3,
    }
    with pytest.raises(ValidationError):
        A2ARequest.model_validate(invalid_req_data)


def test_content_type_not_supported_error():
    # Test ContentTypeNotSupportedError
    err = ContentTypeNotSupportedError(
        code=-32005, message='Incompatible content types'
    )
    assert err.code == -32005
    assert err.message == 'Incompatible content types'
    assert err.data is None

    with pytest.raises(ValidationError):  # Wrong code
        ContentTypeNotSupportedError(
            code=-32000,  # type: ignore
            message='Incompatible content types',
        )

    ContentTypeNotSupportedError(
        code=-32005,
        message='Incompatible content types',
        extra='extra',  # type: ignore
    )


def test_task_not_found_error():
    # Test TaskNotFoundError
    err2 = TaskNotFoundError(
        code=-32001, message='Task not found', data={'taskId': 'abc'}
    )
    assert err2.code == -32001
    assert err2.message == 'Task not found'
    assert err2.data == {'taskId': 'abc'}

    with pytest.raises(ValidationError):  # Wrong code
        TaskNotFoundError(code=-32000, message='Task not found')  # type: ignore

    TaskNotFoundError(code=-32001, message='Task not found', extra='extra')  # type: ignore


def test_push_notification_not_supported_error():
    # Test PushNotificationNotSupportedError
    err3 = PushNotificationNotSupportedError(data={'taskId': 'abc'})
    assert err3.code == -32003
    assert err3.message == 'Push Notification is not supported'
    assert err3.data == {'taskId': 'abc'}

    with pytest.raises(ValidationError):  # Wrong code
        PushNotificationNotSupportedError(
            code=-32000,  # type: ignore
            message='Push Notification is not available',
        )
    with pytest.raises(ValidationError):  # Extra field
        PushNotificationNotSupportedError(
            code=-32001,
            message='Push Notification is not available',
            extra='extra',  # type: ignore
        )


def test_internal_error():
    # Test InternalError
    err_internal = InternalError()
    assert err_internal.code == -32603
    assert err_internal.message == 'Internal error'
    assert err_internal.data is None

    err_internal_data = InternalError(
        code=-32603, message='Internal error', data={'details': 'stack trace'}
    )
    assert err_internal_data.data == {'details': 'stack trace'}

    with pytest.raises(ValidationError):  # Wrong code
        InternalError(code=-32000, message='Internal error')  # type: ignore

    InternalError(code=-32603, message='Internal error', extra='extra')  # type: ignore


def test_invalid_params_error():
    # Test InvalidParamsError
    err_params = InvalidParamsError()
    assert err_params.code == -32602
    assert err_params.message == 'Invalid parameters'
    assert err_params.data is None

    err_params_data = InvalidParamsError(
        code=-32602, message='Invalid parameters', data=['param1', 'param2']
    )
    assert err_params_data.data == ['param1', 'param2']

    with pytest.raises(ValidationError):  # Wrong code
        InvalidParamsError(code=-32000, message='Invalid parameters')  # type: ignore

    InvalidParamsError(
        code=-32602,
        message='Invalid parameters',
        extra='extra',  # type: ignore
    )


def test_invalid_request_error():
    # Test InvalidRequestError
    err_request = InvalidRequestError()
    assert err_request.code == -32600
    assert err_request.message == 'Request payload validation error'
    assert err_request.data is None

    err_request_data = InvalidRequestError(data={'field': 'missing'})
    assert err_request_data.data == {'field': 'missing'}

    with pytest.raises(ValidationError):  # Wrong code
        InvalidRequestError(
            code=-32000,  # type: ignore
            message='Request payload validation error',
        )

    InvalidRequestError(
        code=-32600,
        message='Request payload validation error',
        extra='extra',  # type: ignore
    )  # type: ignore


def test_json_parse_error():
    # Test JSONParseError
    err_parse = JSONParseError(code=-32700, message='Invalid JSON payload')
    assert err_parse.code == -32700
    assert err_parse.message == 'Invalid JSON payload'
    assert err_parse.data is None

    err_parse_data = JSONParseError(data={'foo': 'bar'})  # Explicit None data
    assert err_parse_data.data == {'foo': 'bar'}

    with pytest.raises(ValidationError):  # Wrong code
        JSONParseError(code=-32000, message='Invalid JSON payload')  # type: ignore

    JSONParseError(code=-32700, message='Invalid JSON payload', extra='extra')  # type: ignore


def test_method_not_found_error():
    # Test MethodNotFoundError
    err_parse = MethodNotFoundError()
    assert err_parse.code == -32601
    assert err_parse.message == 'Method not found'
    assert err_parse.data is None

    err_parse_data = JSONParseError(data={'foo': 'bar'})
    assert err_parse_data.data == {'foo': 'bar'}

    with pytest.raises(ValidationError):  # Wrong code
        JSONParseError(code=-32000, message='Invalid JSON payload')  # type: ignore

    JSONParseError(code=-32700, message='Invalid JSON payload', extra='extra')  # type: ignore


def test_task_not_cancelable_error():
    # Test TaskNotCancelableError
    err_parse = TaskNotCancelableError()
    assert err_parse.code == -32002
    assert err_parse.message == 'Task cannot be canceled'
    assert err_parse.data is None

    err_parse_data = JSONParseError(
        data={'foo': 'bar'}, message='not cancelled'
    )
    assert err_parse_data.data == {'foo': 'bar'}
    assert err_parse_data.message == 'not cancelled'

    with pytest.raises(ValidationError):  # Wrong code
        JSONParseError(code=-32000, message='Task cannot be canceled')  # type: ignore

    JSONParseError(
        code=-32700,
        message='Task cannot be canceled',
        extra='extra',  # type: ignore
    )


def test_unsupported_operation_error():
    # Test UnsupportedOperationError
    err_parse = UnsupportedOperationError()
    assert err_parse.code == -32004
    assert err_parse.message == 'This operation is not supported'
    assert err_parse.data is None

    err_parse_data = JSONParseError(
        data={'foo': 'bar'}, message='not supported'
    )
    assert err_parse_data.data == {'foo': 'bar'}
    assert err_parse_data.message == 'not supported'

    with pytest.raises(ValidationError):  # Wrong code
        JSONParseError(code=-32000, message='Unsupported')  # type: ignore

    JSONParseError(code=-32700, message='Unsupported', extra='extra')  # type: ignore


# --- Test TaskIdParams ---


def test_task_id_params_valid():
    """Tests successful validation of TaskIdParams."""
    # Minimal valid data
    params_min = TaskIdParams(**MINIMAL_TASK_ID_PARAMS)
    assert params_min.id == 'task-123'
    assert params_min.metadata is None

    # Full valid data
    params_full = TaskIdParams(**FULL_TASK_ID_PARAMS)
    assert params_full.id == 'task-456'
    assert params_full.metadata == {'source': 'test'}


def test_task_id_params_invalid():
    """Tests validation errors for TaskIdParams."""
    # Missing required 'id' field
    with pytest.raises(ValidationError) as excinfo_missing:
        TaskIdParams()  # type: ignore
    assert 'id' in str(
        excinfo_missing.value
    )  # Check that 'id' is mentioned in the error

    invalid_data = MINIMAL_TASK_ID_PARAMS.copy()
    invalid_data['extra_field'] = 'allowed'
    TaskIdParams(**invalid_data)  # type: ignore

    # Incorrect type for metadata (should be dict)
    invalid_metadata_type = {'id': 'task-789', 'metadata': 'not_a_dict'}
    with pytest.raises(ValidationError) as excinfo_type:
        TaskIdParams(**invalid_metadata_type)  # type: ignore
    assert 'metadata' in str(
        excinfo_type.value
    )  # Check that 'metadata' is mentioned


def test_task_push_notification_config() -> None:
    """Tests successful validation of TaskPushNotificationConfig."""
    auth_info_dict: dict[str, Any] = {
        'schemes': ['Bearer', 'Basic'],
        'credentials': 'user:pass',
    }
    auth_info = PushNotificationAuthenticationInfo(**auth_info_dict)

    push_notification_config = PushNotificationConfig(
        url='https://example.com', token='token', authentication=auth_info
    )
    assert push_notification_config.url == 'https://example.com'
    assert push_notification_config.token == 'token'
    assert push_notification_config.authentication == auth_info

    task_push_notification_config = TaskPushNotificationConfig(
        taskId='task-123', pushNotificationConfig=push_notification_config
    )
    assert task_push_notification_config.taskId == 'task-123'
    assert (
        task_push_notification_config.pushNotificationConfig
        == push_notification_config
    )
    assert task_push_notification_config.model_dump(exclude_none=True) == {
        'taskId': 'task-123',
        'pushNotificationConfig': {
            'url': 'https://example.com',
            'token': 'token',
            'authentication': {
                'schemes': ['Bearer', 'Basic'],
                'credentials': 'user:pass',
            },
        },
    }


def test_jsonrpc_message_valid():
    """Tests successful validation of JSONRPCMessage."""
    # With string ID
    msg_str_id = JSONRPCMessage(jsonrpc='2.0', id='req-1')
    assert msg_str_id.jsonrpc == '2.0'
    assert msg_str_id.id == 'req-1'

    # With integer ID (will be coerced to float by Pydantic for JSON number compatibility)
    msg_int_id = JSONRPCMessage(jsonrpc='2.0', id=1)
    assert msg_int_id.jsonrpc == '2.0'
    assert (
        msg_int_id.id == 1
    )  # Pydantic v2 keeps int if possible, but float is in type hint

    rpc_message = JSONRPCMessage(id=1)
    assert rpc_message.jsonrpc == '2.0'
    assert rpc_message.id == 1


def test_jsonrpc_message_invalid():
    """Tests validation errors for JSONRPCMessage."""
    # Incorrect jsonrpc version
    with pytest.raises(ValidationError):
        JSONRPCMessage(jsonrpc='1.0', id=1)  # type: ignore

    JSONRPCMessage(jsonrpc='2.0', id=1, extra_field='extra')  # type: ignore

    # Invalid ID type (e.g., list) - Pydantic should catch this based on type hints
    with pytest.raises(ValidationError):
        JSONRPCMessage(jsonrpc='2.0', id=[1, 2])  # type: ignore


def test_file_base_valid():
    """Tests successful validation of FileBase."""
    # No optional fields
    base1 = FileBase()
    assert base1.mimeType is None
    assert base1.name is None

    # With mimeType only
    base2 = FileBase(mimeType='image/png')
    assert base2.mimeType == 'image/png'
    assert base2.name is None

    # With name only
    base3 = FileBase(name='document.pdf')
    assert base3.mimeType is None
    assert base3.name == 'document.pdf'

    # With both fields
    base4 = FileBase(mimeType='application/json', name='data.json')
    assert base4.mimeType == 'application/json'
    assert base4.name == 'data.json'


def test_file_base_invalid():
    """Tests validation errors for FileBase."""
    FileBase(extra_field='allowed')  # type: ignore

    # Incorrect type for mimeType
    with pytest.raises(ValidationError) as excinfo_type_mime:
        FileBase(mimeType=123)  # type: ignore
    assert 'mimeType' in str(excinfo_type_mime.value)

    # Incorrect type for name
    with pytest.raises(ValidationError) as excinfo_type_name:
        FileBase(name=['list', 'is', 'wrong'])  # type: ignore
    assert 'name' in str(excinfo_type_name.value)


def test_part_base_valid() -> None:
    """Tests successful validation of PartBase."""
    # No optional fields (metadata is None)
    base1 = PartBase()
    assert base1.metadata is None

    # With metadata
    meta_data: dict[str, Any] = {'source': 'test', 'timestamp': 12345}
    base2 = PartBase(metadata=meta_data)
    assert base2.metadata == meta_data


def test_part_base_invalid():
    """Tests validation errors for PartBase."""
    PartBase(extra_field='allowed')  # type: ignore

    # Incorrect type for metadata (should be dict)
    with pytest.raises(ValidationError) as excinfo_type:
        PartBase(metadata='not_a_dict')  # type: ignore
    assert 'metadata' in str(excinfo_type.value)


def test_a2a_error_validation_and_serialization() -> None:
    """Tests validation and serialization of the A2AError RootModel."""

    # 1. Test JSONParseError
    json_parse_instance = JSONParseError()
    json_parse_data = json_parse_instance.model_dump(exclude_none=True)
    a2a_err_parse = A2AError.model_validate(json_parse_data)
    assert isinstance(a2a_err_parse.root, JSONParseError)

    # 2. Test InvalidRequestError
    invalid_req_instance = InvalidRequestError()
    invalid_req_data = invalid_req_instance.model_dump(exclude_none=True)
    a2a_err_invalid_req = A2AError.model_validate(invalid_req_data)
    assert isinstance(a2a_err_invalid_req.root, InvalidRequestError)

    # 3. Test MethodNotFoundError
    method_not_found_instance = MethodNotFoundError()
    method_not_found_data = method_not_found_instance.model_dump(
        exclude_none=True
    )
    a2a_err_method = A2AError.model_validate(method_not_found_data)
    assert isinstance(a2a_err_method.root, MethodNotFoundError)

    # 4. Test InvalidParamsError
    invalid_params_instance = InvalidParamsError()
    invalid_params_data = invalid_params_instance.model_dump(exclude_none=True)
    a2a_err_params = A2AError.model_validate(invalid_params_data)
    assert isinstance(a2a_err_params.root, InvalidParamsError)

    # 5. Test InternalError
    internal_err_instance = InternalError()
    internal_err_data = internal_err_instance.model_dump(exclude_none=True)
    a2a_err_internal = A2AError.model_validate(internal_err_data)
    assert isinstance(a2a_err_internal.root, InternalError)

    # 6. Test TaskNotFoundError
    task_not_found_instance = TaskNotFoundError(data={'taskId': 't1'})
    task_not_found_data = task_not_found_instance.model_dump(exclude_none=True)
    a2a_err_task_nf = A2AError.model_validate(task_not_found_data)
    assert isinstance(a2a_err_task_nf.root, TaskNotFoundError)

    # 7. Test TaskNotCancelableError
    task_not_cancelable_instance = TaskNotCancelableError()
    task_not_cancelable_data = task_not_cancelable_instance.model_dump(
        exclude_none=True
    )
    a2a_err_task_nc = A2AError.model_validate(task_not_cancelable_data)
    assert isinstance(a2a_err_task_nc.root, TaskNotCancelableError)

    # 8. Test PushNotificationNotSupportedError
    push_not_supported_instance = PushNotificationNotSupportedError()
    push_not_supported_data = push_not_supported_instance.model_dump(
        exclude_none=True
    )
    a2a_err_push_ns = A2AError.model_validate(push_not_supported_data)
    assert isinstance(a2a_err_push_ns.root, PushNotificationNotSupportedError)

    # 9. Test UnsupportedOperationError
    unsupported_op_instance = UnsupportedOperationError()
    unsupported_op_data = unsupported_op_instance.model_dump(exclude_none=True)
    a2a_err_unsupported = A2AError.model_validate(unsupported_op_data)
    assert isinstance(a2a_err_unsupported.root, UnsupportedOperationError)

    # 10. Test ContentTypeNotSupportedError
    content_type_err_instance = ContentTypeNotSupportedError()
    content_type_err_data = content_type_err_instance.model_dump(
        exclude_none=True
    )
    a2a_err_content = A2AError.model_validate(content_type_err_data)
    assert isinstance(a2a_err_content.root, ContentTypeNotSupportedError)

    # 11. Test invalid data (doesn't match any known error code/structure)
    invalid_data: dict[str, Any] = {'code': -99999, 'message': 'Unknown error'}
    with pytest.raises(ValidationError):
        A2AError.model_validate(invalid_data)
