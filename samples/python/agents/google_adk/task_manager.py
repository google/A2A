import json
import logging

from abc import ABC, abstractmethod
from collections.abc import AsyncIterable
from typing import Any

from common.server import utils
from common.server.task_manager import InMemoryTaskManager
from common.types import (
    SendTaskRequest,  # deprecated
    TaskSendParams,  # deprecated
    Message,
    TaskStatus,
    Artifact,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    TaskState,
    Task,
    SendTaskResponse,  # deprecated
    InternalError,
    JSONRPCResponse,
    SendTaskStreamingRequest,  # deprecated
    SendTaskStreamingResponse,  # deprecated
    SendMessageRequest,
    SendMessageResponse,
    SendMessageStreamRequest,
    SendMessageStreamResponse,
    MessageSendParams,
)
from google.genai import types
from typing import Union
import logging
import uuid

logger = logging.getLogger(__name__)


# TODO: Move this class (or these classes) to a common directory
class AgentWithTaskManager(ABC):
    @abstractmethod
    def get_processing_message(self) -> str:
        pass

    def invoke(self, query, session_id) -> str:
        session = self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )
        content = types.Content(
            role='user', parts=[types.Part.from_text(text=query)]
        )
        if session is None:
            session = self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )
        events = list(
            self._runner.run(
                user_id=self._user_id,
                session_id=session.id,
                new_message=content,
            )
        )
        if not events or not events[-1].content or not events[-1].content.parts:
            return ''
        return '\n'.join([p.text for p in events[-1].content.parts if p.text])

    async def stream(self, query, session_id) -> AsyncIterable[dict[str, Any]]:
        session = self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )
        content = types.Content(
            role='user', parts=[types.Part.from_text(text=query)]
        )
        if session is None:
            session = self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )
        async for event in self._runner.run_async(
            user_id=self._user_id, session_id=session.id, new_message=content
        ):
            if event.is_final_response():
                response = ''
                if (
                    event.content
                    and event.content.parts
                    and event.content.parts[0].text
                ):
                    response = '\n'.join(
                        [p.text for p in event.content.parts if p.text]
                    )
                elif (
                    event.content
                    and event.content.parts
                    and any(
                        [
                            True
                            for p in event.content.parts
                            if p.function_response
                        ]
                    )
                ):
                    response = next(
                        (
                            p.function_response.model_dump()
                            for p in event.content.parts
                        )
                    )
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

    # deprecated
    async def _stream_generator(
        self, request: SendTaskStreamingRequest
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        task_send_params: TaskSendParams = request.params
        query = self._get_user_query(task_send_params)
        try:
            async for item in self.agent.stream(
                query, task_send_params.sessionId
            ):
                is_task_complete = item['is_task_complete']
                artifacts = None
                if not is_task_complete:
                    task_state = TaskState.WORKING
                    parts = [{'type': 'text', 'text': item['updates']}]
                else:
                    if isinstance(item['content'], dict):
                        if (
                            'response' in item['content']
                            and 'result' in item['content']['response']
                        ):
                            data = json.loads(
                                item['content']['response']['result']
                            )
                            task_state = TaskState.INPUT_REQUIRED
                        else:
                            data = item['content']
                            task_state = TaskState.COMPLETED
                        parts = [{'type': 'data', 'data': data}]
                    else:
                        task_state = TaskState.COMPLETED
                        parts = [{'type': 'text', 'text': item['content']}]
                    artifacts = [Artifact(parts=parts, index=0, append=False)]
            message = Message(role='agent', parts=parts)
            task_status = TaskStatus(state=task_state, message=message)
            await self._update_store(
                task_send_params.id, task_status, artifacts
            )
            task_update_event = TaskStatusUpdateEvent(
                id=task_send_params.id,
                status=task_status,
                final=False,
            )
            yield SendTaskStreamingResponse(
                id=request.id, result=task_update_event
            )
            # Now yield Artifacts too
            if artifacts:
                for artifact in artifacts:
                    yield SendTaskStreamingResponse(
                        id=request.id,
                        result=TaskArtifactUpdateEvent(
                            id=task_send_params.id,
                            artifact=artifact,
                        ),
                    )
            if is_task_complete:
                yield SendTaskStreamingResponse(
                    id=request.id,
                    result=TaskStatusUpdateEvent(
                        id=task_send_params.id,
                        status=TaskStatus(
                            state=task_status.state,
                        ),
                        final=True,
                    ),
                )
        except Exception as e:
            logger.error(f'An error occurred while streaming the response: {e}')
            yield JSONRPCResponse(
                id=request.id,
                error=InternalError(
                    message='An error occurred while streaming the response'
                ),
            )

    def _validate_request(
        self,
        request: Union[
            SendTaskRequest,
            SendTaskStreamingRequest,
            SendMessageRequest,
            SendMessageStreamRequest,
        ],
    ) -> None:
        invalidModes = self._validate_output_modes(
            request, self.agent.SUPPORTED_CONTENT_TYPES
        )
        if invalidModes:
            logger.warning(invalidModes.error)

    async def _stream_message_generator(
        self, request: SendMessageStreamRequest
    ) -> AsyncIterable[SendMessageStreamResponse] | JSONRPCResponse:
        send_params: MessageSendParams = request.params
        query = self._get_user_query(send_params)
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
            async for item in self.agent.stream(query, contextId):
                is_task_complete = item['is_task_complete']
                artifacts = None
                if not is_task_complete:
                    task_state = TaskState.WORKING
                    parts = [{'type': 'text', 'text': item['updates']}]
                else:
                    if isinstance(item['content'], dict):
                        if (
                            'response' in item['content']
                            and 'result' in item['content']['response']
                        ):
                            data = json.loads(
                                item['content']['response']['result']
                            )
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
            yield SendMessageStreamResponse(
                id=request.id, result=task_update_event
            )
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
            logger.error(f'An error occurred while streaming the response: {e}')
            yield JSONRPCResponse(
                id=request.id,
                error=InternalError(
                    message=f'An error occurred while streaming the response {e}'
                ),
            )

    # deprecated
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        error = self._validate_request(request)
        if error:
            return error
        await self.upsert_task(request.params)
        return await self._invoke(request)

    async def on_send_message(
        self, request: SendMessageRequest
    ) -> SendMessageResponse:
        error = self._validate_request(request)
        if error:
            return error

        taskId, contextId = self._extract_task_and_context(request.params)
        request.params.message.taskId = taskId
        request.params.message.contextId = contextId
        await self.upsert_task(request.params)
        return await self._send(request)

    # deprecated
    async def on_send_task_subscribe(
        self, request: SendTaskStreamingRequest
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        error = self._validate_request(request)
        if error:
            return error
        await self.upsert_task(request.params)
        return self._stream_generator(request)

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

    # deprecated
    async def _invoke(self, request: SendTaskRequest) -> SendTaskResponse:
        task_send_params: TaskSendParams = request.params
        query = self._get_user_query(task_send_params)
        try:
            result = self.agent.invoke(query, task_send_params.sessionId)
        except Exception as e:
            logger.error(f'Error invoking agent: {e}')
            raise ValueError(f'Error invoking agent: {e}')
        parts = [{'type': 'text', 'text': result}]
        task_state = (
            TaskState.INPUT_REQUIRED
            if 'MISSING_INFO:' in result
            else TaskState.COMPLETED
        )
        task = await self._update_store(
            task_send_params.id,
            TaskStatus(
                state=task_state, message=Message(role='agent', parts=parts)
            ),
            [Artifact(parts=parts)],
        )
        return SendTaskResponse(id=request.id, result=task)

    async def _send(self, request: SendMessageRequest) -> SendMessageResponse:
        message: MessageSendParams = request.params
        query = self._get_user_query(message)
        contextId = (
            message.message.contextId
            if message.message.contextId
            else str(uuid.uuid4())
        )
        taskId = (
            message.message.taskId
            if message.message.taskId
            else str(uuid.uuid4())
        )
        try:
            result = self.agent.invoke(query, contextId)
        except Exception as e:
            logger.error(f'Error invoking agent: {e}')
            raise ValueError(f'Error invoking agent: {e}') from e

        parts = [{'type': 'text', 'text': result}]
        task_state = (
            TaskState.INPUT_REQUIRED
            if 'MISSING_INFO:' in result
            else TaskState.COMPLETED
        )
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
                )
                if task_state == TaskState.INPUT_REQUIRED
                else None,
            ),
            [Artifact(parts=parts)]
            if task_state == TaskState.COMPLETED
            else [],
        )
        return SendMessageResponse(id=request.id, result=task)
