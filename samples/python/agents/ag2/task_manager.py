from typing import AsyncIterable
from common.types import (
    SendTaskRequest,
    TaskSendParams,
    Message,
    TaskStatus,
    Artifact,
    TextPart,
    TaskState,
    SendTaskResponse,
    InternalError,
    JSONRPCResponse,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent
)
from common.server.task_manager import InMemoryTaskManager
from .agent import YoutubeMCPAgent
import common.server.utils as utils
import asyncio
import logging
import traceback

logger = logging.getLogger(__name__)


class AgentTaskManager(InMemoryTaskManager):
    """Task manager for AG2 MCP agent."""
    
    def __init__(self, agent: YoutubeMCPAgent):
        super().__init__()
        self.agent = agent

    # -------------------------------------------------------------
    # Public API methods
    # -------------------------------------------------------------

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
            agent_response = self.agent.invoke(query, task_send_params.sessionId)
            return await self._handle_send_task(request, agent_response)
        except Exception as e:
            logger.error(f"Error invoking agent: {e}")
            return SendTaskResponse(
                id=request.id, 
                error=InternalError(message=f"Error during on_send_task: {str(e)}")
            )

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
            sse_event_queue = await self.setup_sse_consumer(task_send_params.id, False)            

            asyncio.create_task(self._handle_send_task_streaming(request))

            return self.dequeue_events_for_sse(
                request.id, task_send_params.id, sse_event_queue
            )
        except Exception as e:
            logger.error(f"Error in SSE stream: {e}")
            print(traceback.format_exc())
            return JSONRPCResponse(
                id=request.id,
                error=InternalError(
                    message="An error occurred while streaming the response"
                ),
            )

    # -------------------------------------------------------------
    # Agent response handlers
    # -------------------------------------------------------------

    async def _handle_send_task(
        self, request: SendTaskRequest, agent_response: dict
    ) -> SendTaskResponse:
        """
        Handle the 'tasks/send' JSON-RPC method by processing agent response.
        
        This method processes the synchronous (one-time) response from the agent,
        transforms it into the appropriate task status and artifacts, and 
        returns a complete SendTaskResponse.
        """
        task_send_params: TaskSendParams = request.params
        task_id = task_send_params.id
        history_length = task_send_params.historyLength
        task_status = None

        parts = [TextPart(type="text", text=agent_response["content"])]
        artifact = None
        if agent_response["require_user_input"]:
            task_status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message=Message(role="agent", parts=parts),
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
        return SendTaskResponse(id=request.id, result=task_result)

    async def _handle_send_task_streaming(self, request: SendTaskStreamingRequest):
        """
        Handle the 'tasks/sendSubscribe' JSON-RPC method for streaming responses.
        
        This method processes streaming responses from the agent incrementally,
        converting each chunk into appropriate SSE events for real-time client updates.
        It handles different agent response states (working, input required, completed)
        and generates both status update and artifact events.
        """
        task_send_params: TaskSendParams = request.params
        query = self._extract_user_query(task_send_params)

        try:
            async for item in self.agent.stream(query, task_send_params.sessionId):
                is_task_complete = item["is_task_complete"]
                require_user_input = item["require_user_input"]
                content = item["content"]
                
                logger.info(f"Stream item received: complete={is_task_complete}, require_input={require_user_input}, content_len={len(content)}")
                
                artifact = None
                message = None
                parts = [TextPart(type="text", text=content)]
                end_stream = False

                if not is_task_complete and not require_user_input:
                    # Processing message - working state
                    task_state = TaskState.WORKING
                    message = Message(role="agent", parts=parts)
                    logger.info(f"Sending WORKING status update")
                elif require_user_input:
                    # Requires user input - input required state
                    task_state = TaskState.INPUT_REQUIRED
                    message = Message(role="agent", parts=parts)
                    end_stream = True
                    logger.info(f"Sending INPUT_REQUIRED status update (final)")
                else:
                    # Task completed - completed state with artifact
                    task_state = TaskState.COMPLETED
                    artifact = Artifact(parts=parts, index=0, append=False)
                    end_stream = True
                    logger.info(f"Sending COMPLETED status with artifact (final)")

                # Update task store (return value not used)
                task_status = TaskStatus(state=task_state, message=message)
                await self.update_store(
                    task_send_params.id,
                    task_status,
                    None if artifact is None else [artifact],
                )

                # First send artifact if we have one
                if artifact:
                    logger.info(f"Sending artifact event for task {task_send_params.id}")
                    task_artifact_update_event = TaskArtifactUpdateEvent(
                        id=task_send_params.id, artifact=artifact
                    )
                    await self.enqueue_events_for_sse(
                        task_send_params.id, task_artifact_update_event
                    )                    
                
                # Then send status update
                logger.info(f"Sending status update for task {task_send_params.id}, state={task_state}, final={end_stream}")
                task_update_event = TaskStatusUpdateEvent(
                    id=task_send_params.id, status=task_status, final=end_stream
                )
                await self.enqueue_events_for_sse(
                    task_send_params.id, task_update_event
                )

        except Exception as e:
            logger.error(f"An error occurred while streaming the response: {e}")
            logger.error(traceback.format_exc())
            await self.enqueue_events_for_sse(
                task_send_params.id,
                InternalError(message=f"An error occurred while streaming the response: {e}")                
            )

    # -------------------------------------------------------------
    # Utility methods
    # -------------------------------------------------------------

    def _validate_request(
        self, request: SendTaskRequest | SendTaskStreamingRequest
    ) -> JSONRPCResponse | None:
        """
        Validate task request parameters for compatibility with agent capabilities.
        
        Ensures that the client's requested output modalities are compatible with
        what the agent can provide.
        
        Returns:
            JSONRPCResponse with an error if validation fails, None otherwise.
        """
        task_send_params: TaskSendParams = request.params
        if not utils.are_modalities_compatible(
            task_send_params.acceptedOutputModes, YoutubeMCPAgent.SUPPORTED_CONTENT_TYPES
        ):
            logger.warning(
                "Unsupported output mode. Received %s, Support %s",
                task_send_params.acceptedOutputModes,
                YoutubeMCPAgent.SUPPORTED_CONTENT_TYPES,
            )
            return utils.new_incompatible_types_error(request.id)
        return None
        
    def _extract_user_query(self, task_send_params: TaskSendParams) -> str:
        """
        Extract the user's text query from the task parameters.
        
        Extracts and returns the text content from the first part of the user's message.
        Currently only supports text parts.
        
        Args:
            task_send_params: The parameters of the task containing the user's message.
            
        Returns:
            str: The extracted text query.
            
        Raises:
            ValueError: If the message part is not a TextPart.
        """
        part = task_send_params.message.parts[0]
        if not isinstance(part, TextPart):
            raise ValueError("Only text parts are supported")
        return part.text