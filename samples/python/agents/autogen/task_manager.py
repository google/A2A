"""
Task manager for the A2A AutoGen Weather Agent server.
"""

import asyncio
import logging
from typing import AsyncIterable, Union

from common.server.task_manager import InMemoryTaskManager
from common.types import (
    SendTaskRequest,
    TaskSendParams,
    Message,
    TaskStatus,
    Artifact,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    TextPart,
    TaskState,
    Task,
    SendTaskResponse,
    InternalError,
    JSONRPCResponse,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
)
import common.server.utils as utils

from agent import WeatherAgent

logger = logging.getLogger(__name__)


class WeatherTaskManager(InMemoryTaskManager):
    """Task manager that integrates AutoGen's WeatherAgent with the A2A protocol."""

    def __init__(self, api_key: str | None = None):
        """Initialize the task manager with AutoGen components."""
        super().__init__()
        self.agent = WeatherAgent(api_key=api_key)

    async def _stream_generator(
        self, request: SendTaskStreamingRequest
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        task_send_params: TaskSendParams = request.params
        query = self._get_user_query(task_send_params)
        try:
            # Process stream from agent
            async for item in self.agent.stream(query, task_send_params.sessionId):
                is_task_complete = item["is_task_complete"] 
                
                if not is_task_complete:
                    # Progress updates
                    task_state = TaskState.WORKING
                    parts = [{"type": "text", "text": item["content"]}]
                else:
                    # Final response
                    task_state = TaskState.COMPLETED
                    parts = [{"type": "text", "text": item["content"]}]
                    artifacts = [Artifact(parts=parts, index=0, append=False)]
                
                # Create message and status update
                message = Message(role="agent", parts=parts)
                task_status = TaskStatus(state=task_state, message=message)
                
                # Update task store
                await self.update_store(
                    task_send_params.id, 
                    task_status,  
                )
                
                # Send status update to client - mark as final if complete
                yield SendTaskStreamingResponse(
                    id=request.id,
                    result=TaskStatusUpdateEvent(
                        id=task_send_params.id,
                        status=task_status,
                        final=is_task_complete,
                    ),
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
        self, request: Union[SendTaskRequest, SendTaskStreamingRequest]
    ) -> JSONRPCResponse | None:
        """Validate that the request is compatible with our capabilities."""
        task_send_params: TaskSendParams = request.params
        if not utils.are_modalities_compatible(
            task_send_params.acceptedOutputModes, 
            self.agent.SUPPORTED_CONTENT_TYPES
        ):
            logger.warning(
                "Unsupported output mode. Received %s, Support %s",
                task_send_params.acceptedOutputModes,
                self.agent.SUPPORTED_CONTENT_TYPES,
            )
            return utils.new_incompatible_types_error(request.id)
        return None
    
    def _get_user_query(self, task_send_params: TaskSendParams) -> str:
        """Extract the text query from the task parameters."""
        part = task_send_params.message.parts[0]
        if not isinstance(part, TextPart):
            raise ValueError("Only text parts are supported")
        return part.text

    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """Handle non-streaming task requests."""
        error = self._validate_request(request)
        if error:
            return error
        await self.upsert_task(request.params)
        return await self._invoke(request)

    async def on_send_task_subscribe(
        self, request: SendTaskStreamingRequest
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        """Handle streaming task requests."""
        error = self._validate_request(request)
        if error:
            return error
        await self.upsert_task(request.params)
        return self._stream_generator(request)

    async def update_store(
        self, task_id: str, status: TaskStatus, artifacts: list[Artifact] = None
    ) -> Task:
        """Update the task store with the new status and artifacts."""
        async with self.lock:
            try:
                task = self.tasks[task_id]
            except KeyError:
                logger.error(f"Task {task_id} not found for updating the task")
                raise ValueError(f"Task {task_id} not found")
            
            task.status = status
            
            if artifacts is not None:
                if task.artifacts is None:
                    task.artifacts = []
                task.artifacts.extend(artifacts)
            
            return task

    async def _invoke(self, request: SendTaskRequest) -> SendTaskResponse:
        """Process a non-streaming request and return the result."""
        task_send_params: TaskSendParams = request.params
        query = self._get_user_query(task_send_params)
        
        try:
            # Set initial status to working
            await self.update_store(
                task_send_params.id, 
                TaskStatus(state=TaskState.WORKING)
            )
            
            # Get response from the agent
            response_content = await self.agent.invoke(query, task_send_params.sessionId)
            
            # Create artifact and update task status
            parts = [{"type": "text", "text": response_content}]
            
            task = await self.update_store(
                task_send_params.id,
                TaskStatus(
                    state=TaskState.COMPLETED, 
                    message=Message(role="agent", parts=parts)
                ),
                [Artifact(parts=parts)],
            )
            
            return SendTaskResponse(id=request.id, result=task)
        except Exception as e:
            logger.error(f"Error invoking agent: {e}")
            return SendTaskResponse(
                id=request.id,
                error=InternalError(message=f"Error invoking agent: {e}")
            )