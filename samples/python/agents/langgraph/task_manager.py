from typing import AsyncIterable
from common.types import (
    SendTaskRequest,  # deprecated
    TaskSendParams,  # deprecated
    Message,
    TaskStatus,
    Artifact,
    TaskState,
    SendTaskResponse,  # deprecated
    InternalError,
    JSONRPCResponse,
    SendTaskStreamingRequest,  # deprecated
    SendTaskStreamingResponse,  # deprecated
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    Task,
    TaskIdParams,
    PushNotificationConfig,
    InvalidParamsError,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageStreamRequest,
    SendMessageStreamResponse,
    MessageSendParams,
)
from common.server.task_manager import InMemoryTaskManager
from agents.langgraph.agent import CurrencyAgent
from common.utils.push_notification_auth import PushNotificationSenderAuth
from typing import Union
import asyncio
import logging
import traceback
import uuid

logger = logging.getLogger(__name__)


class AgentTaskManager(InMemoryTaskManager):
    def __init__(
        self,
        agent: CurrencyAgent,
        notification_sender_auth: PushNotificationSenderAuth,
    ):
        super().__init__()
        self.agent = agent
        self.notification_sender_auth = notification_sender_auth

    # deprecated
    async def _run_streaming_agent(self, request: SendTaskStreamingRequest):
        task_send_params: TaskSendParams = request.params
        query = self._get_user_query(task_send_params)

        try:
            async for item in self.agent.stream(
                query, task_send_params.sessionId
            ):
                is_task_complete = item['is_task_complete']
                require_user_input = item['require_user_input']
                artifact = None
                message = None
                parts = [{'type': 'text', 'text': item['content']}]
                end_stream = False

                if not is_task_complete and not require_user_input:
                    task_state = TaskState.WORKING
                    message = Message(role='agent', parts=parts)
                elif require_user_input:
                    task_state = TaskState.INPUT_REQUIRED
                    message = Message(role='agent', parts=parts)
                    end_stream = True
                else:
                    task_state = TaskState.COMPLETED
                    artifact = Artifact(parts=parts, index=0, append=False)
                    end_stream = True

                task_status = TaskStatus(state=task_state, message=message)
                latest_task = await self.update_store(
                    task_send_params.id,
                    task_status,
                    None if artifact is None else [artifact],
                )
                await self.send_task_notification(latest_task)

                if artifact:
                    task_artifact_update_event = TaskArtifactUpdateEvent(
                        id=task_send_params.id, artifact=artifact
                    )
                    await self.enqueue_events_for_sse(
                        task_send_params.id, task_artifact_update_event
                    )

                task_update_event = TaskStatusUpdateEvent(
                    id=task_send_params.id, status=task_status, final=end_stream
                )
                await self.enqueue_events_for_sse(
                    task_send_params.id, task_update_event
                )

        except Exception as e:
            logger.error(f'An error occurred while streaming the response: {e}')
            await self.enqueue_events_for_sse(
                task_send_params.id,
                InternalError(
                    message=f'An error occurred while streaming the response: {e}'
                ),
            )

    async def _run_message_stream_agent(
        self, request: SendMessageStreamRequest
    ):
        params: MessageSendParams = request.params
        query = self._get_user_query(params)
        # Extract task and context id from request, if provided else generate.
        taskId, contextId = self._extract_task_and_context(request.params)

        try:
            # If this is a new task, emit it first
            if params.message.taskId is None:
                params.message.taskId = taskId
                params.message.contextId = contextId
                task = Task(
                    id=taskId,
                    contextId=contextId,
                    status=TaskStatus(
                        state=TaskStatus.SUBMITTED,
                        message=params.message,
                    ),
                    history=[params.message],
                )
                self.tasks[taskId] = task
                await self.enqueue_events_for_sse(taskId, task)

            async for item in self.agent.stream(query, contextId):
                is_task_complete = item['is_task_complete']
                require_user_input = item['require_user_input']
                artifact = None
                message = None
                parts = [{'type': 'text', 'text': item['content']}]
                end_stream = False

                if not is_task_complete and not require_user_input:
                    task_state = TaskState.WORKING
                    message = Message(
                        role='agent',
                        parts=parts,
                        messageId=str(uuid.uuid4()),
                        taskId=taskId,
                        contextId=contextId,
                    )
                elif require_user_input:
                    task_state = TaskState.INPUT_REQUIRED
                    message = Message(
                        role='agent',
                        parts=parts,
                        messageId=str(uuid.uuid4()),
                        taskId=taskId,
                        contextId=contextId,
                    )
                    end_stream = True
                else:
                    task_state = TaskState.COMPLETED
                    artifact = Artifact(parts=parts, index=0, append=False)
                    end_stream = True

                task_status = TaskStatus(state=task_state, message=message)
                latest_task = await self.update_store(
                    taskId,
                    task_status,
                    None if artifact is None else [artifact],
                )
                await self.send_task_notification(latest_task)

                if artifact:
                    task_artifact_update_event = TaskArtifactUpdateEvent(
                        id=taskId,
                        artifact=artifact,
                        contextId=contextId,
                    )
                    await self.enqueue_events_for_sse(
                        taskId, task_artifact_update_event
                    )

                task_update_event = TaskStatusUpdateEvent(
                    id=taskId,
                    status=task_status,
                    final=end_stream,
                    contextId=contextId,
                )
                await self.enqueue_events_for_sse(taskId, task_update_event)

        except Exception as e:
            logger.error(f'An error occurred while streaming the response: {e}')
            await self.enqueue_events_for_sse(
                taskId,
                InternalError(
                    message=f'An error occurred while streaming the response: {e}'
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
    ) -> JSONRPCResponse | None:
        modeValidation = self._validate_output_modes(
            request, CurrencyAgent.SUPPORTED_CONTENT_TYPES
        )
        if modeValidation:
            return modeValidation
        return self._validate_push_config(request)

    # deprecated
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """Handles the 'send task' request."""
        validation_error = self._validate_request(request)
        if validation_error:
            return SendTaskResponse(id=request.id, error=validation_error.error)

        if request.params.pushNotification:
            if not await self.set_push_notification_info(
                request.params.id, request.params.pushNotification
            ):
                return SendTaskResponse(
                    id=request.id,
                    error=InvalidParamsError(
                        message='Push notification URL is invalid'
                    ),
                )

        await self.upsert_task(request.params)
        task = await self.update_store(
            request.params.id, TaskStatus(state=TaskState.WORKING), None
        )
        await self.send_task_notification(task)

        task_send_params: TaskSendParams = request.params
        query = self._get_user_query(task_send_params)
        try:
            agent_response = self.agent.invoke(
                query, task_send_params.sessionId
            )
        except Exception as e:
            logger.error(f'Error invoking agent: {e}')
            raise ValueError(f'Error invoking agent: {e}')
        return await self._process_agent_response(request, agent_response)

    async def on_send_message(
        self, request: SendMessageRequest
    ) -> SendMessageResponse:
        """Handles the 'send message' request."""
        validation_error = self._validate_request(request)
        if validation_error:
            return SendMessageResponse(
                id=request.id, error=validation_error.error
            )

        if request.params.pushNotification:
            if not await self.set_push_notification_info(
                request.params.id, request.params.pushNotification
            ):
                return SendMessageResponse(
                    id=request.id,
                    error=InvalidParamsError(
                        message='Push notification URL is invalid'
                    ),
                )
        taskId, contextId = self._extract_task_and_context(request.params)

        await self.upsert_task(request.params)
        task = await self.update_store(
            request.params.id, TaskStatus(state=TaskState.WORKING), None
        )
        await self.send_task_notification(task)

        params: MessageSendParams = request.params
        query = self._get_user_query(params)
        try:
            agent_response = self.agent.invoke(query, params.contextId)
        except Exception as e:
            logger.error(f'Error invoking agent: {e}')
            raise ValueError(f'Error invoking agent: {e}')
        # TODO: Once the task/send is removed, update process_agent_response
        # to return the SendMessageResponse. Instead, now, we extract the task
        # from the response and construct the correct type.
        response = await self._process_agent_response(request, agent_response)
        return SendMessageResponse(id=response.id, result=response.result)

    # deprecated
    async def on_send_task_subscribe(
        self, request: SendTaskStreamingRequest
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        try:
            error = self._validate_request(request)
            if error:
                return error

            await self.upsert_task(request.params)

            if request.params.pushNotification:
                if not await self.set_push_notification_info(
                    request.params.id, request.params.pushNotification
                ):
                    return JSONRPCResponse(
                        id=request.id,
                        error=InvalidParamsError(
                            message='Push notification URL is invalid'
                        ),
                    )

            task_send_params: TaskSendParams = request.params
            sse_event_queue = await self.setup_sse_consumer(
                task_send_params.id, False
            )

            asyncio.create_task(self._run_streaming_agent(request))

            return self.dequeue_events_for_sse(
                request.id, task_send_params.id, sse_event_queue
            )
        except Exception as e:
            logger.error(f'Error in SSE stream: {e}')
            print(traceback.format_exc())
            return JSONRPCResponse(
                id=request.id,
                error=InternalError(
                    message='An error occurred while streaming the response'
                ),
            )

    async def on_send_message_stream(
        self, request: SendMessageStreamRequest
    ) -> AsyncIterable[SendMessageStreamResponse] | JSONRPCResponse:
        try:
            error = self._validate_request(request)
            if error:
                return error
            task_id, context_id = self._extract_task_and_context(request.params)
            request.params.message.taskId = task_id
            request.params.message.contextId = context_id
            task = await self.upsert_task(request.params)
            if request.params.configuration.pushNotification:
                if not await self.set_push_notification_info(
                    task.id, request.params.configuration.pushNotification
                ):
                    return JSONRPCResponse(
                        id=request.id,
                        error=InvalidParamsError(
                            message='Push notification URL is invalid'
                        ),
                    )

            sse_event_queue = await self.setup_sse_consumer(
                task_id,
                False,
            )

            asyncio.create_task(self._run_message_stream_agent(request))

            return self.dequeue_message_events_for_sse(
                request.id, task.id, sse_event_queue
            )
        except Exception as e:
            logger.error(f'Error in SSE stream: {e}')
            print(traceback.format_exc())
            return JSONRPCResponse(
                id=request.id,
                error=InternalError(
                    message='An error occurred while streaming the response'
                ),
            )

    async def _process_agent_response(
        self, request: SendTaskRequest, agent_response: dict
    ) -> SendTaskResponse:
        """Processes the agent's response and updates the task store."""
        task_send_params: TaskSendParams = request.params
        task_id = task_send_params.id
        history_length = task_send_params.historyLength
        task_status = None

        parts = [{'type': 'text', 'text': agent_response['content']}]
        artifact = None
        if agent_response['require_user_input']:
            task_status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message=Message(role='agent', parts=parts),
            )
        else:
            task_status = TaskStatus(state=TaskState.COMPLETED)
            artifact = Artifact(parts=parts)
        task = await self.update_store(
            task_id, task_status, None if artifact is None else [artifact]
        )
        task_result = self.append_task_history(task, history_length)
        await self.send_task_notification(task)
        return SendTaskResponse(id=request.id, result=task_result)

    async def send_task_notification(self, task: Task):
        if not await self.has_push_notification_info(task.id):
            logger.info(f'No push notification info found for task {task.id}')
            return
        push_info = await self.get_push_notification_info(task.id)

        logger.info(f'Notifying for task {task.id} => {task.status.state}')
        await self.notification_sender_auth.send_push_notification(
            push_info.url, data=task.model_dump(exclude_none=True)
        )

    async def on_resubscribe_to_task(
        self, request
    ) -> AsyncIterable[SendMessageStreamResponse] | JSONRPCResponse:
        task_id_params: TaskIdParams = request.params
        try:
            sse_event_queue = await self.setup_sse_consumer(
                task_id_params.id, True
            )
            return self.dequeue_message_events_for_sse(
                request.id, task_id_params.id, sse_event_queue
            )
        except Exception as e:
            logger.error(f'Error while reconnecting to SSE stream: {e}')
            return JSONRPCResponse(
                id=request.id,
                error=InternalError(
                    message=f'An error occurred while reconnecting to stream: {e}'
                ),
            )

    async def set_push_notification_info(
        self, task_id: str, push_notification_config: PushNotificationConfig
    ):
        # Verify the ownership of notification URL by issuing a challenge request.
        is_verified = (
            await self.notification_sender_auth.verify_push_notification_url(
                push_notification_config.url
            )
        )
        if not is_verified:
            return False

        await super().set_push_notification_info(
            task_id, push_notification_config
        )
        return True
