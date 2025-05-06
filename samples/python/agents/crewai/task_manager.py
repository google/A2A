"""Agent Task Manager."""

import logging

from collections.abc import AsyncIterable

from agent import ImageGenerationAgent
from common.server.task_manager import InMemoryTaskManager
from common.types import (
    Artifact,
    FileContent,
    FilePart,
    JSONRPCResponse,
    SendTaskRequest,  # deprecated
    SendTaskResponse,  # deprecated
    SendTaskStreamingRequest,  # deprecated
    SendTaskStreamingResponse,  # deprecated
    Task,
    TaskSendParams,  # deprecated
    TaskState,
    TaskStatus,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageStreamRequest,
    SendMessageStreamResponse,
)


logger = logging.getLogger(__name__)


class AgentTaskManager(InMemoryTaskManager):
    """Agent Task Manager, handles task routing and response packing."""

    def __init__(self, agent: ImageGenerationAgent):
        super().__init__()
        self.agent = agent

    async def _stream_generator(
        self, request: SendTaskRequest
    ) -> AsyncIterable[SendTaskResponse]:
        raise NotImplementedError('Not implemented')

    # deprecated
    async def on_send_task(
        self, request: SendTaskRequest
    ) -> SendTaskResponse | AsyncIterable[SendTaskResponse]:
        ## only support text output at the moment
        validateOutputModes = self._validate_output_modes(
            request, ImageGenerationAgent.SUPPORTED_CONTENT_TYPES
        )
        if validateOutputModes:
            return validateOutputModes

        task_send_params: TaskSendParams = request.params
        await self.upsert_task(task_send_params)

        return await self._invoke(request)

    async def on_send_message(
        self, request: SendMessageRequest
    ) -> SendMessageResponse:
        ## only support text output at the moment
        validateOutputModes = self._validate_output_modes(
            request, ImageGenerationAgent.SUPPORTED_CONTENT_TYPES
        )
        if validateOutputModes:
            return validateOutputModes

        taskId, contextId = self._extract_task_and_context(request.params)
        request.params.message.taskId = taskId
        request.params.message.contextId = contextId
        await self.upsert_task(request.params)

        # Repackage the SendTaskResponse as SendMessageReponse
        response = await self._invoke(request)
        return SendMessageResponse(id=response.id, result=response.result)

    # deprecated
    async def on_send_task_subscribe(
        self, request: SendTaskStreamingRequest
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        error = self._validate_request(request)
        if error:
            return error

        await self.upsert_task(request.params)

    async def on_send_message_stream(
        self, request: SendMessageStreamRequest
    ) -> AsyncIterable[SendMessageStreamResponse] | JSONRPCResponse:
        error = self._validate_request(request)
        if error:
            yield error
            return

        taskId, contextId = self._extract_task_and_context(request.params)
        request.params.message.taskId = taskId
        request.params.message.contextId = contextId
        await self.upsert_task(request.params)
        response = await self._invoke(request)
        yield SendMessageStreamResponse(id=response.id, result=response.result)

    async def _update_store(
        self, task_id: str, status: TaskStatus, artifacts: list[Artifact]
    ) -> Task:
        async with self.lock:
            try:
                task = self.tasks[task_id]
            except KeyError as exc:
                logger.error('Task %s not found for updating the task', task_id)
                raise ValueError(f'Task {task_id} not found') from exc

            task.status = status

            if status.message is not None:
                self.task_messages[task_id].append(status.message)

            if artifacts is not None:
                if task.artifacts is None:
                    task.artifacts = []
                task.artifacts.extend(artifacts)

            return task

    async def _invoke(
        self, request: SendTaskRequest | SendMessageRequest
    ) -> SendTaskResponse:
        # task_send_params: TaskSendParams = request.params
        query = self._get_user_query(request.params)
        task_id, context_id = self._extract_task_and_context(request.params)
        try:
            result = self.agent.invoke(query, context_id)
            print(f'Final Result ===> {result}')
        except Exception as e:
            logger.error('Error invoking agent: %s', e)
            raise ValueError(f'Error invoking agent: {e}') from e

        data = self.agent.get_image_data(
            session_id=context_id, image_key=result.raw
        )
        if data and not data.error:
            parts = [
                FilePart(
                    file=FileContent(
                        bytes=data.bytes, mimeType=data.mime_type, name=data.id
                    )
                )
            ]
        else:
            parts = [
                {
                    'type': 'text',
                    'text': data.error if data else 'failed to generate image',
                }
            ]

        task = await self._update_store(
            task_id,
            TaskStatus(state=TaskState.COMPLETED),
            [Artifact(parts=parts)],
        )
        return SendTaskResponse(id=request.id, result=task)
