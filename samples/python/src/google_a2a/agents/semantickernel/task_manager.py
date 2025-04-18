import asyncio
import logging
from typing import AsyncIterable

from common.server.task_manager import InMemoryTaskManager
from common.types import (
    Artifact,
    InternalError,
    InvalidParamsError,
    JSONRPCResponse,
    Message,
    SendTaskRequest,
    SendTaskResponse,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from common.utils.push_notification_auth import PushNotificationSenderAuth

from agents.semantickernel.agent import SemanticKernelTravelAgent

logger = logging.getLogger(__name__)


class TaskManager(InMemoryTaskManager):
    """A TaskManager used for the Semantic Kernel Agent sample."""

    def __init__(self, notification_sender_auth: PushNotificationSenderAuth):
        """Initialize the TaskManager with a notification sender."""
        super().__init__()
        self.agent = SemanticKernelTravelAgent()
        self.notification_sender_auth = notification_sender_auth

    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """A method to handle a task request.
        
        Args:
            request: The task request containing the parameters.

        Returns:
            SendTaskResponse: The response containing the task ID and status.
        """
        validation_error = self._validate_request(request)
        if validation_error:
            return SendTaskResponse(id=request.id, error=validation_error.error)

        await self.upsert_task(request.params)
        task = await self.update_store(request.params.id, TaskStatus(state=TaskState.WORKING), None)
        await self.send_task_notification(task)

        query = request.params.message.parts[0].text
        try:
            agent_response = await self.agent.invoke(query, request.params.sessionId)
        except Exception as e:
            logger.error(f"Semantic Kernel Task Manager error: {e}")
            raise ValueError(f"Agent error: {e}")

        return await self._process_agent_response(request, agent_response)

    async def on_send_task_subscribe(
        self, request: SendTaskStreamingRequest
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        """A method to handle a task streaming request.
        
        Args:
            request: The task streaming request containing the parameters.

        Returns:
            AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse: The streaming response or error.
        """
        try:
            error = self._validate_request(request)
            if error:
                return error

            await self.upsert_task(request.params)
            sse_queue = await self.setup_sse_consumer(request.params.id, False)
            asyncio.create_task(self._run_streaming_agent(request))
            return self.dequeue_events_for_sse(request.id, request.params.id, sse_queue)
        except Exception as e:
            logger.error(f"Error in SSE stream: {e}")
            return JSONRPCResponse(
                id=request.id,
                error=InternalError(message="Error in streaming response"),
            )

    async def _run_streaming_agent(self, request: SendTaskStreamingRequest) -> AsyncIterable[SendTaskStreamingResponse]:
        """A method to run the streaming agent.
        
        Args:
            request: The task streaming request containing the parameters.

        Yields:
            AsyncIterable[SendTaskStreamingResponse]: The streaming response.
        """
        try:
            query = request.params.message.parts[0].text
            async for partial in self.agent.stream(query, request.params.sessionId):
                require_input = partial["require_user_input"]
                is_done = partial["is_task_complete"]
                text_content = partial["content"]
                artifact = None

                new_status = TaskStatus(state=TaskState.WORKING)
                # By default, don't end the stream
                final = False

                if require_input:
                    new_status.state = TaskState.INPUT_REQUIRED
                    new_status.message = Message(
                        role="agent",
                        parts=[{"type": "text", "text": text_content}],
                    )
                    # End the stream if we need user input
                    final = True
                elif is_done:
                    new_status.state = TaskState.COMPLETED
                    artifact = Artifact(parts=[{"type": "text", "text": text_content}], index=0, append=False)
                    # End the stream if the agent is fully done
                    final = True
                else:
                    # Still "WORKING"
                    new_status.message = Message(
                        role="agent",
                        parts=[{"type": "text", "text": text_content}],
                    )

                if artifact:
                    task_artifact_update_event = TaskArtifactUpdateEvent(
                        id=request.params.id, artifact=artifact
                    )
                    await self.enqueue_events_for_sse(
                        request.params.id, task_artifact_update_event
                    )

                # Persist + notify
                updated_task = await self.update_store(request.params.id, new_status, [artifact] if artifact else None)
                await self.send_task_notification(updated_task)

                await self.enqueue_events_for_sse(
                    request.params.id,
                    TaskStatusUpdateEvent(id=request.params.id, status=new_status, final=final),
                )

                if final:
                    break

        except Exception as e:
            logger.error(f"Streaming agent encountered error: {e}")
            await self.enqueue_events_for_sse(
                request.params.id, InternalError(message=f"Error while streaming: {e}")
            )

    async def _process_agent_response(self, request: SendTaskRequest, agent_response: dict) -> SendTaskResponse:
        """Process the agent's response and update the task status.
        
        Args:
            request: The task request containing the parameters.
            agent_response: The response from the agent.

        Returns:
            SendTaskResponse: The response containing the task ID and status.
        """
        parts = [{"type": "text", "text": agent_response["content"]}]
        if agent_response["require_user_input"]:
            task_status = TaskStatus(state=TaskState.INPUT_REQUIRED, message=Message(role="agent", parts=parts))
        else:
            task_status = TaskStatus(state=TaskState.COMPLETED)
        artifact = Artifact(parts=parts) if not agent_response["require_user_input"] else None

        updated_task = await self.update_store(request.params.id, task_status, [artifact] if artifact else None)
        await self.send_task_notification(updated_task)
        return SendTaskResponse(id=request.id, result=updated_task)

    def _validate_request(self, request: SendTaskStreamingRequest) -> JSONRPCResponse | None:
        """Validate the request parameters.
        
        Args:
            request: The task request containing the parameters.

        Returns:
            JSONRPCResponse: The response containing the error if validation fails.
        """
        if not request.params.acceptedOutputModes:
            return None
        if not any(
            mode in SemanticKernelTravelAgent.SUPPORTED_CONTENT_TYPES for mode in request.params.acceptedOutputModes
        ):
            logger.warning("Incompatible content type for SK Agent.")
            return JSONRPCResponse(id=request.id, error=InvalidParamsError(message="Bad content type."))
        return None

    async def send_task_notification(self, task: SendTaskRequest) -> None:
        """Send a push notification for the task.
        
        Args:
            task: The task object containing the parameters.
        """
        if not await self.has_push_notification_info(task.id):
            return
        push_info = await self.get_push_notification_info(task.id)
        await self.notification_sender_auth.send_push_notification(
            push_info.url, data=task.model_dump(exclude_none=True)
        )
