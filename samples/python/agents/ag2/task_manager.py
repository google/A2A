from typing import AsyncIterable
from common.types import (
    SendTaskRequest,  # deprecated
    TaskSendParams,  # deprecated
    Message,
    TaskStatus,
    Artifact,
    TextPart,
    TaskState,
    SendTaskResponse,  # deprecated
    InternalError,
    JSONRPCResponse,
    SendTaskStreamingRequest,  # deprecated
    SendTaskStreamingResponse,  # deprecated
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageStreamRequest,
    SendMessageStreamResponse,
    Task,
)
from common.server.task_manager import InMemoryTaskManager
from .agent import YoutubeMCPAgent
import common.server.utils as utils
import asyncio
import logging
import traceback
import uuid

logger = logging.getLogger(__name__)


class AgentTaskManager(InMemoryTaskManager):
    """Task manager for AG2 MCP agent."""

    def __init__(self, agent: YoutubeMCPAgent):
        super().__init__()
        self.agent = agent

    # -------------------------------------------------------------
    # Public API methods
    # -------------------------------------------------------------

    # deprecated
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """
        Handle synchronous task requests.

        This method processes one-time task requests and returns a complete response.
        Unlike streaming tasks, this waits for the full agent response before returning.
        """
        validation_error = self._validate_request(request)
        if validation_error:
            return SendTaskResponse(id=request.id, error=validation_error.error)

        await self.upsert_task(request.params)
        # Update task store to WORKING state (return value not used)
        await self.update_store(
            request.params.id, TaskStatus(state=TaskState.WORKING), None
        )

        task_send_params: TaskSendParams = request.params
        query = self._extract_user_query(task_send_params)

        try:
            agent_response = self.agent.invoke(
                query, task_send_params.sessionId
            )
            task = await self._handle_send_task(request, agent_response)
            return SendTaskResponse(id=request.id, result=task)
        except Exception as e:
            logger.error(f'Error invoking agent: {e}')
            return SendTaskResponse(
                id=request.id,
                error=InternalError(
                    message=f'Error during on_send_task: {str(e)}'
                ),
            )

    async def on_send_message(
        self, request: SendMessageRequest
    ) -> SendMessageResponse:
        """
        Handle synchronous task requests.

        This method processes one-time task requests and returns a complete response.
        Unlike streaming tasks, this waits for the full agent response before returning.
        """
        validation_error = self._validate_request(request)
        if validation_error:
            return SendMessageResponse(
                id=request.id, error=validation_error.error
            )

        task_id, context_id = self._extract_task_and_context(request.params)
        request.params.message.taskId = task_id
        request.params.message.contextId = context_id
        await self.upsert_task(request.params)
        # Update task store to WORKING state (return value not used)
        await self.update_store(
            task_id, TaskStatus(state=TaskState.WORKING), None
        )

        query = self._extract_user_query(request.params)

        try:
            agent_response = self.agent.invoke(query, context_id)
            task = await self._handle_send_task(request, agent_response)
            return SendMessageResponse(id=request.id, result=task)
        except Exception as e:
            logger.error(f'Error invoking agent: {e}')
            return SendTaskResponse(
                id=request.id,
                error=InternalError(
                    message=f'Error during on_send_task: {str(e)}'
                ),
            )

    # deprecated
    async def on_send_task_subscribe(
        self, request: SendTaskStreamingRequest
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        """
        Handle streaming task requests with SSE subscription.

        This method initiates a streaming task and returns incremental updates
        to the client as they become available. It uses Server-Sent Events (SSE)
        to push updates to the client as the agent generates them.
        """
        try:
            error = self._validate_request(request)
            if error:
                return error

            await self.upsert_task(request.params)

            task_send_params: TaskSendParams = request.params
            sse_event_queue = await self.setup_sse_consumer(
                task_send_params.id, False
            )

            asyncio.create_task(self._handle_send_task_streaming(request))

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
        """
        Handle streaming message requests with SSE subscription.

        This method initiates a streaming task and returns incremental updates
        to the client as they become available. It uses Server-Sent Events (SSE)
        to push updates to the client as the agent generates them.
        """
        try:
            error = self._validate_request(request)
            if error:
                return error

            task_id, context_id = self._extract_task_and_context(request.params)
            request.params.message.taskId = task_id
            request.params.message.contextId = context_id
            await self.upsert_task(request.params)

            sse_event_queue = await self.setup_sse_consumer(task_id, False)

            asyncio.create_task(self._handle_send_task_streaming(request))

            return self.dequeue_message_events_for_sse(
                request.id, task_id, sse_event_queue
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

    # -------------------------------------------------------------
    # Agent response handlers
    # -------------------------------------------------------------

    async def _handle_send_task(
        self,
        request: SendTaskRequest | SendMessageRequest,
        agent_response: dict,
    ) -> Task:
        """
        Handle the 'tasks/send' JSON-RPC method by processing agent response.

        This method processes the synchronous (one-time) response from the agent,
        transforms it into the appropriate task status and artifacts, and
        returns a complete SendTaskResponse.
        """
        task_id, context_id = self.extract_task_and_context(request.params)
        history_length = -1
        if isinstance(request, SendTaskRequest):
            history_length = request.params.historyLength
        else:
            history_length = request.params.configuration.historyLength
        task_status = None

        parts = [TextPart(type='text', text=agent_response['content'])]
        artifact = None
        if agent_response['require_user_input']:
            task_status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message=Message(
                    role='agent',
                    parts=parts,
                    contextId=context_id,
                    taskId=task_id,
                    messageId=str(uuid.uuid4()),
                ),
            )
        else:
            task_status = TaskStatus(state=TaskState.COMPLETED)
            artifact = Artifact(parts=parts)
        # Update task store and get result for response
        updated_task = await self.update_store(
            task_id, task_status, None if artifact is None else [artifact]
        )
        # Use the updated task to create a response with correct history
        task_result = self.append_task_history(updated_task, history_length)
        return task_result

    async def _handle_send_task_streaming(
        self, request: SendTaskStreamingRequest | SendMessageStreamRequest
    ):
        """
        Handle the 'tasks/sendSubscribe' JSON-RPC method for streaming responses.

        This method processes streaming responses from the agent incrementally,
        converting each chunk into appropriate SSE events for real-time client updates.
        It handles different agent response states (working, input required, completed)
        and generates both status update and artifact events.
        """
        task_id, context_id = self._extract_task_and_context(request.params)
        query = self._extract_user_query(request.params)

        try:
            async for item in self.agent.stream(query, context_id):
                is_task_complete = item['is_task_complete']
                require_user_input = item['require_user_input']
                content = item['content']

                logger.info(
                    f'Stream item received: complete={is_task_complete}, require_input={require_user_input}, content_len={len(content)}'
                )

                artifact = None
                message = None
                parts = [TextPart(type='text', text=content)]
                end_stream = False

                if not is_task_complete and not require_user_input:
                    # Processing message - working state
                    task_state = TaskState.WORKING
                    message = Message(
                        role='agent',
                        parts=parts,
                        taskId=task_id,
                        contextId=context_id,
                        messageId=str(uuid.uuid4()),
                    )
                    logger.info('Sending WORKING status update')
                elif require_user_input:
                    # Requires user input - input required state
                    task_state = TaskState.INPUT_REQUIRED
                    message = Message(
                        role='agent',
                        parts=parts,
                        taskId=task_id,
                        contextId=context_id,
                        messageId=str(uuid.uuid4()),
                    )
                    end_stream = True
                    logger.info('Sending INPUT_REQUIRED status update (final)')
                else:
                    # Task completed - completed state with artifact
                    task_state = TaskState.COMPLETED
                    artifact = Artifact(parts=parts, index=0, append=False)
                    end_stream = True
                    logger.info(
                        'Sending COMPLETED status with artifact (final)'
                    )

                # Update task store (return value not used)
                task_status = TaskStatus(state=task_state, message=message)
                await self.update_store(
                    task_id,
                    task_status,
                    None if artifact is None else [artifact],
                )

                # First send artifact if we have one
                if artifact:
                    logger.info(f'Sending artifact event for task {task_id}')
                    task_artifact_update_event = TaskArtifactUpdateEvent(
                        id=task_id, artifact=artifact
                    )
                    await self.enqueue_events_for_sse(
                        task_id, task_artifact_update_event
                    )

                # Then send status update
                logger.info(
                    f'Sending status update for task {task_id}, state={task_state}, final={end_stream}'
                )
                task_update_event = TaskStatusUpdateEvent(
                    id=task_id,
                    status=task_status,
                    final=end_stream,
                    contextId=context_id,
                )
                await self.enqueue_events_for_sse(task_id, task_update_event)

        except Exception as e:
            logger.error(f'An error occurred while streaming the response: {e}')
            logger.error(traceback.format_exc())
            await self.enqueue_events_for_sse(
                task_id,
                InternalError(
                    message=f'An error occurred while streaming the response: {e}'
                ),
            )

    # -------------------------------------------------------------
    # Utility methods
    # -------------------------------------------------------------

    def _validate_request(
        self,
        request: SendTaskRequest
        | SendTaskStreamingRequest
        | SendMessageRequest
        | SendMessageStreamRequest,
    ) -> JSONRPCResponse | None:
        """
        Validate task request parameters for compatibility with agent capabilities.

        Ensures that the client's requested output modalities are compatible with
        what the agent can provide.

        Returns:
            JSONRPCResponse with an error if validation fails, None otherwise.
        """
        invalidOutput = self._validate_output_modes(
            request, YoutubeMCPAgent.SUPPORTED_CONTENT_TYPES
        )
        if invalidOutput:
            logger.warning(invalidOutput.error)
            return invalidOutput
        return None
