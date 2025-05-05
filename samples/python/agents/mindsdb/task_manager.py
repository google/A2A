from typing import AsyncIterable
from common.types import (
    SendTaskRequest, # deprecated
    Message,
    TaskStatus,
    Artifact,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    TaskState,
    Task,
    SendTaskResponse, # deprecated
    InternalError,
    JSONRPCResponse,
    SendTaskStreamingRequest, # deprecated
    SendTaskStreamingResponse, # deprecated
    SendMessageRequest,
    SendMessageResponse,
    SendMessageStreamRequest,
    SendMessageStreamResponse
)
from common.server.task_manager import InMemoryTaskManager
from agent import MindsDBAgent
from typing import Union
import logging
import uuid
logger = logging.getLogger(__name__)

class AgentTaskManager(InMemoryTaskManager):

    def __init__(self, agent: MindsDBAgent):
        super().__init__()
        self.agent = agent

    async def _stream_generator(
        self, request: SendTaskStreamingRequest | SendMessageStreamRequest
    ) -> AsyncIterable[TaskStatusUpdateEvent | TaskArtifactUpdateEvent] | JSONRPCResponse:
        task_id, context_id = self._extract_task_and_context(request.params)
        query = self._get_user_query(request.params)
        try:
          async for item in self.agent.stream(query, context_id):
            is_task_complete = item["is_task_complete"]
            parts = item["parts"]

            if not is_task_complete:
                task_state = TaskState.WORKING
                metadata = item["metadata"]
                message = Message(
                    role="agent",
                    parts=parts,
                    metadata=metadata,
                    taskId=task_id,
                    contextId=context_id,
                    messageId=str(uuid.uuid4()),
                )
                task_status = TaskStatus(state=task_state, message=message)
                await self._update_store(task_id, task_status, [])
                task_update_event = TaskStatusUpdateEvent(
                    id=task_id,
                    status=task_status,
                    final=False,
                    contextId=context_id,
                )
                yield task_update_event
            else:
                task_state = TaskState.COMPLETED
                artifact = Artifact(parts=parts, index=0, append=False)
                task_status = TaskStatus(state=task_state)
                yield TaskArtifactUpdateEvent(
                      id=task_id,
                      artifact=artifact,
                      contextId=context_id
                )
                await self._update_store(task_id, task_status, [artifact])
                yield TaskStatusUpdateEvent(
                    id=task_id,
                    status=TaskStatus(
                        state=task_status.state,
                    ),
                    final=True,
                    contextId=context_id,
                )

        except Exception as e:
            logger.error(f"An error occurred while streaming the response: {e}")
            yield JSONRPCResponse(
                id=request.id,
                error=InternalError(
                    message="An error occurred while streaming the response"
                ),
            )

    def _validate_request(
        self, request: Union[
            SendTaskRequest, SendTaskStreamingRequest,
            SendMessageRequest, SendMessageStreamRequest]
    ) -> JSONRPCResponse | None:
        invalidOutput = self._validate_output_modes(
            request, MindsDBAgent.SUPPORTED_CONTENT_TYPES)
        if invalidOutput:
            logger.warning(invalidOutput.error)
            return invalidOutput
        return None

    # deprecated
    async def on_send_task(
        self, request: SendTaskRequest
    ) -> SendTaskResponse:
        error = self._validate_request(request)
        if error:
            return error
        await self.upsert_task(request.params)
        task = await self._invoke(request)
        return SendTaskResponse(id=request.id, result=task)

    async def on_send_message(
        self, request: SendMessageRequest
    ) -> SendMessageResponse:
        error = self._validate_request(request)
        if error:
            return error
        task_id, context_id = self._extract_task_and_context(request.params)
        request.params.message.taskId = task_id
        request.params.message.contextId = context_id
        await self.upsert_task(request.params)
        task = await self._invoke(request)
        return SendMessageResponse(id=request.id, result=task)

    # deprecated
    async def on_send_task_subscribe(
        self, request: SendTaskStreamingRequest
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        error = self._validate_request(request)
        if error:
            return error
        task_id, context_id = self._extract_task_and_context(request.params)
        request.params.message.taskId = task_id
        request.params.message.contextId = context_id
        await self.upsert_task(request.params)
        stream = self._stream_generator(request)
        if isinstance(stream, AsyncIterable):
            async def wrap_tasks(stream) -> AsyncIterable[SendTaskStreamingRequest]:
                async for x in stream:
                    yield SendTaskStreamingResponse(id=request.id, result=x)
            return wrap_tasks(stream)
        else:
            return stream

    async def on_send_message_stream(
        self, request: SendMessageStreamRequest
    ) -> AsyncIterable[SendMessageStreamResponse] | JSONRPCResponse:
        error = self._validate_request(request)
        if error:
            return error
        task_id, context_id = self._extract_task_and_context(request.params)
        request.params.message.taskId = task_id
        request.params.message.contextId = context_id
        await self.upsert_task(request.params)
        stream = self._stream_generator(request)
        if isinstance(stream, AsyncIterable):
            async def wrap_tasks(stream) -> AsyncIterable[SendMessageStreamRequest]:
                async for x in stream:
                    yield SendMessageStreamResponse(id=request.id, result=x)
            return wrap_tasks(stream)
        else:
            return stream

    async def _update_store(
        self, task_id: str, status: TaskStatus, artifacts: list[Artifact]
    ) -> Task:
        async with self.lock:
            try:
                task = self.tasks[task_id]
            except KeyError:
                logger.error(f"Task {task_id} not found for updating the task")
                raise ValueError(f"Task {task_id} not found")
            task.status = status
            #if status.message is not None:
            #    self.task_messages[task_id].append(status.message)
            if artifacts is not None:
                if task.artifacts is None:
                    task.artifacts = []
                task.artifacts.extend(artifacts)
            return task

    async def _invoke(self, request: SendTaskRequest | SendMessageRequest) -> Task:
        task_id, context_id = self._extract_task_and_context(request.params)
        query = self._get_user_query(request.params)
        try:
            result = self.agent.invoke(query, context_id)
        except Exception as e:
            logger.error(f"Error invoking agent: {e}")
            raise ValueError(f"Error invoking agent: {e}")
        parts = [{"type": "text", "text": result}]
        task_state = TaskState.INPUT_REQUIRED if "MISSING_INFO:" in result else TaskState.COMPLETED
        task = await self._update_store(
            task_id,
            TaskStatus(
                state=task_state,
                message=Message(
                    role="agent",
                    parts=parts,
                    taskId=task_id,
                    contextId=context_id,
                    message_id=str(uuid.uuid4()),
                )
            ),
            [Artifact(parts=parts)],
        )
        return task
