import json
import logging
import time
import traceback
import uuid

from abc import ABC, abstractmethod
from collections.abc import AsyncIterable
from typing import Any

from common.server.task_manager import InMemoryTaskManager
from common.types import (
    A2AClientError,
    Artifact,
    InternalError,
    JSONRPCResponse,
    Message,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageStreamRequest,
    SendMessageStreamResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)
from google.adk.events import Event, EventActions
from google.adk.sessions import BaseSessionService, Session
from google.genai import types


logger = logging.getLogger(__name__)


def get_a2a_client_error(event: Event) -> A2AClientError | None:
    # To handle authentication failures, we need to see if there is a function_response event whose result
    # corresponds with an A2AClientError and its status_code=401
    a2a_authn_keys = {'data', 'message', 'status_code'}
    a2a_client_error = next(
        (
            response
            for part in event.content.parts
            if (response := getattr(part.function_response, 'response', None))
            and isinstance(response, dict)
            and a2a_authn_keys.issubset(response)
        ),
        None,
    )

    # If there is an A2A authentication error, return a corresponding A2AClientError
    if a2a_client_error:
        a2a_error_message = a2a_client_error['message']

        if isinstance(a2a_client_error['data'], dict) and 'reason' in a2a_client_error['data']:
            a2a_error_message = a2a_client_error['data']['reason']

        return A2AClientError(
            data=a2a_client_error['data'],
            message=a2a_error_message,
            status_code=a2a_client_error['status_code'],
        )

    return None


def get_session(session_service: BaseSessionService, app_name: str, user_id: str, session_id: str) -> Session:
    session = session_service.get_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )
    if session is None:
        session = session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            state={},
            session_id=session_id,
        )

    return session


def update_session_state(author: str, changes: dict[str, Any], session: Session, session_service: BaseSessionService):
    changes['session_active'] = True

    # --- Create Event with Actions ---
    actions_with_update = EventActions(state_delta=changes)
    # This event might represent an internal system action, not just an agent response
    system_event = Event(
        author=author,
        actions=actions_with_update,
        timestamp=time.time(),
    )

    # --- Append the Event (This updates the state) ---
    session_service.append_event(session, system_event)


# TODO: Move this class (or these classes) to a common directory
class AgentWithTaskManager(ABC):
    def __init__(self):
        # This is not production quality, just a simple way to store credentials to be passed to the agent context
        self._credentials = None
        self._task_manager = None

    @abstractmethod
    def get_processing_message(self) -> str:
        pass

    def update_credentials(self, credentials: dict[str, Any]):
        self._credentials = credentials

    def invoke(self, send_params, session_id) -> str:
        query = self._task_manager._get_user_query(send_params)
        session = get_session(self._runner.session_service, self._agent.name, self._user_id, session_id)
        content = types.Content(role='user', parts=[types.Part.from_text(text=query)])
        state_changes = {}

        if self._credentials:
            state_changes['user:credentials'] = self._credentials

        if send_params.message.metadata and 'oauth_callback' in send_params.message.metadata:
            state_changes['oauth_callback'] = send_params.message.metadata['oauth_callback']

        if state_changes:
            update_session_state(self._agent.name, state_changes, session, self._runner.session_service)

        events = list(
            self._runner.run(
                user_id=self._user_id,
                session_id=session.id,
                new_message=content,
            )
        )

        # If there's no content or parts in the last event, return empty string
        last_event = events[-1] if events else None
        if not last_event or not last_event.content or not last_event.content.parts:
            return ''

        # To handle authentication failures, we need to see if there is a function_response event whose result
        # corresponds with an A2AClientError and its status_code=401
        a2a_client_error = get_a2a_client_error(last_event)

        # If there is an A2A authentication error, return a corresponding A2AClientError
        if a2a_client_error:
            raise a2a_client_error

        # Handle function call responses
        if last_event.content and last_event.content.parts and last_event.content.parts[0].function_response:
            fr_res = last_event.content.parts[0].function_response.response

            if isinstance(fr_res, dict):
                return fr_res['result']

            return fr_res

        # Concatenate all text parts from the final event
        return '\n'.join(part.text for part in last_event.content.parts if part.text)

    async def stream(self, send_params, session_id) -> AsyncIterable[dict[str, Any]]:
        session = get_session(self._runner.session_service, self._agent.name, self._user_id, session_id)
        query = self._task_manager._get_user_query(send_params)
        content = types.Content(role='user', parts=[types.Part.from_text(text=query)])
        state_changes = {}

        if self._credentials:
            state_changes['user:credentials'] = self._credentials

        if send_params.message.metadata and 'oauth_callback' in send_params.message.metadata:
            state_changes['oauth_callback'] = send_params.message.metadata['oauth_callback']

        if state_changes:
            update_session_state(self._agent.name, state_changes, session, self._runner.session_service)

        async for event in self._runner.run_async(user_id=self._user_id, session_id=session.id, new_message=content):
            a2a_client_error = get_a2a_client_error(event)

            if a2a_client_error:
                yield {
                    'is_task_complete': False,
                    'auth_required': True,
                    'updates': a2a_client_error.data['hint'],
                    'state': a2a_client_error.data['state'],
                }
            elif event.is_final_response():
                response = ''
                if event.content and event.content.parts and event.content.parts[0].text:
                    response = '\n'.join([p.text for p in event.content.parts if p.text])
                elif (
                    event.content
                    and event.content.parts
                    and any([True for p in event.content.parts if p.function_response])
                ):
                    response = next((p.function_response.model_dump() for p in event.content.parts))
                yield {
                    'is_task_complete': True,
                    'content': response,
                }
            else:
                yield {
                    'is_task_complete': False,
                    'updates': self.get_processing_message(),
                }


class AgentTaskManager(InMemoryTaskManager):
    def __init__(self, agent: AgentWithTaskManager):
        super().__init__()
        self.agent = agent
        self.agent._task_manager = self

    def _validate_request(
        self,
        request: SendMessageRequest | SendMessageStreamRequest,
    ) -> None:
        invalidModes = self._validate_output_modes(request, self.agent.SUPPORTED_CONTENT_TYPES)
        if invalidModes:
            logger.warning(invalidModes.error)

    async def _stream_message_generator(
        self, request: SendMessageStreamRequest
    ) -> AsyncIterable[SendMessageStreamResponse] | JSONRPCResponse:
        send_params: MessageSendParams = request.params
        taskId, contextId = self._extract_task_and_context(send_params)
        try:
            # If this is a new task, emit it first
            if send_params.message.taskId is None:
                send_params.message.taskId = taskId
                send_params.message.contextId = contextId
                task = Task(
                    id=taskId,
                    contextId=contextId,
                    status=TaskStatus(
                        state=TaskStatus.SUBMITTED,
                        message=send_params.message,
                    ),
                    history=[send_params.message],
                )
                self.tasks[taskId] = task
                yield SendMessageStreamRequest(id=request.id, result=task)
            async for item in self.agent.stream(send_params, contextId):
                is_task_complete = item['is_task_complete']
                artifacts = None
                if not is_task_complete:
                    if item.get('auth_required'):
                        task_state = TaskState.AUTH_REQUIRED
                    elif item.get('input_required'):
                        task_state = TaskState.INPUT_REQUIRED
                    else:
                        task_state = TaskState.WORKING
                    parts = [{'type': 'text', 'text': item['updates']}]
                else:
                    if isinstance(item['content'], dict):
                        if 'response' in item['content'] and 'result' in item['content']['response']:
                            data = json.loads(item['content']['response']['result'])
                            task_state = TaskState.INPUT_REQUIRED
                        else:
                            data = item['content']
                            task_state = TaskState.COMPLETED
                        parts = [{'type': 'data', 'data': data}]
                    else:
                        task_state = TaskState.COMPLETED
                        parts = [{'type': 'text', 'text': item['content']}]
                    artifacts = [Artifact(parts=parts, index=0, append=False)]
            message = Message(
                role='agent',
                parts=parts,
                messageId=str(uuid.uuid4()),
                taskId=taskId,
                contextId=contextId,
            )
            task_status = TaskStatus(state=task_state, message=message)
            await self._update_store(taskId, task_status, artifacts)
            task_update_event = TaskStatusUpdateEvent(
                id=taskId,
                contextId=contextId,
                status=task_status,
                final=False,
            )
            yield SendMessageStreamResponse(id=request.id, result=task_update_event)
            # Now yield Artifacts too
            if artifacts:
                for artifact in artifacts:
                    yield SendMessageStreamResponse(
                        id=request.id,
                        result=TaskArtifactUpdateEvent(
                            id=taskId,
                            contextId=contextId,
                            artifact=artifact,
                        ),
                    )
            if is_task_complete:
                yield SendMessageStreamResponse(
                    id=request.id,
                    result=TaskStatusUpdateEvent(
                        id=taskId,
                        contextId=contextId,
                        status=TaskStatus(
                            state=task_status.state,
                        ),
                        final=True,
                    ),
                )
        except Exception as e:
            traceback.print_exc()
            logger.error(f'An error occurred while streaming the response: {e}')
            yield JSONRPCResponse(
                id=request.id,
                error=InternalError(message=f'An error occurred while streaming the response {e}'),
            )

    async def on_send_message(self, request: SendMessageRequest) -> SendMessageResponse:
        error = self._validate_request(request)
        if error:
            return error

        taskId, contextId = self._extract_task_and_context(request.params)
        request.params.message.taskId = taskId
        request.params.message.contextId = contextId
        await self.upsert_task(request.params)
        return await self._send(request)

    async def on_send_message_stream(
        self, request: SendMessageStreamRequest
    ) -> AsyncIterable[SendMessageStreamResponse] | JSONRPCResponse:
        error = self._validate_request(request)
        if error:
            return error
        taskId, contextId = self._extract_task_and_context(request.params)
        request.params.message.taskId = taskId
        request.params.message.contextId = contextId
        await self.upsert_task(request.params)
        return self._stream_message_generator(request)

    async def _send(self, request: SendMessageRequest) -> SendMessageResponse:
        send_params: MessageSendParams = request.params
        contextId = send_params.message.contextId if send_params.message.contextId else str(uuid.uuid4())
        taskId = send_params.message.taskId if send_params.message.taskId else str(uuid.uuid4())
        try:
            result = self.agent.invoke(send_params, contextId)
            metadata = None
            parts = [{'type': 'text', 'text': result}]
            task_state = TaskState.INPUT_REQUIRED if 'MISSING_INFO:' in result else TaskState.COMPLETED
        except A2AClientError as e:
            logger.info(f'A2AClientError: {e}')
            metadata = e.data
            metadata['status_code'] = e.status_code
            if e.status_code in (401, 403):
                parts = [{'type': 'text', 'text': e.data['hint']}]
            else:
                parts = [{'type': 'text', 'text': e.message}]
            task_state = TaskState.AUTH_REQUIRED if e.status_code in (401, 403) else TaskState.FAILED
        except Exception as e:
            logger.error(f'Error invoking agent: {e}')
            raise ValueError(f'Error invoking agent: {e}') from e

        task = await self._update_store(
            taskId,
            TaskStatus(
                state=task_state,
                message=Message(
                    role='agent',
                    parts=parts,
                    contextId=contextId,
                    messageId=str(uuid.uuid4()),
                    taskId=taskId,
                    metadata=metadata,
                )
                if task_state in (TaskState.AUTH_REQUIRED, TaskState.INPUT_REQUIRED)
                else None,
            ),
            [Artifact(parts=parts)] if task_state == TaskState.COMPLETED else [],
        )

        return SendMessageResponse(id=request.id, result=task)
