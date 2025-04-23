import asyncio
import logging
import traceback
from collections.abc import AsyncIterable
from typing import Any

import common.server.utils as utils
from agents.marvin.agent import ExtractorAgent
from common.server.task_manager import InMemoryTaskManager
from common.types import (
    Artifact,
    DataPart,
    InternalError,
    InvalidParamsError,
    JSONRPCResponse,
    Message,
    PushNotificationConfig,
    SendTaskRequest,
    SendTaskResponse,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskIdParams,
    TaskSendParams,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)
from common.utils.push_notification_auth import PushNotificationSenderAuth

logger = logging.getLogger(__name__)


class AgentTaskManager(InMemoryTaskManager):
    def __init__(
        self,
        agent: ExtractorAgent,
        notification_sender_auth: PushNotificationSenderAuth,
    ):
        super().__init__()
        self.agent = agent
        self.notification_sender_auth = notification_sender_auth

    def _parse_agent_outcome(
        self, agent_outcome: dict[str, Any]
    ) -> tuple[TaskStatus, list[Artifact]]:
        """Parses the dictionary output from agent.invoke() into A2A TaskStatus and Artifacts."""
        is_task_complete = agent_outcome["is_task_complete"]
        require_user_input = not is_task_complete
        data = agent_outcome.get("data", {})
        text_parts = agent_outcome.get("text_parts", [])
        print(f"Data: {data}")
        parts = []
        parts.extend(text_parts)

        if data:
            parts.append(DataPart(type="data", data=data))

        task_status: TaskStatus | None = None
        artifacts: list[Artifact] = []

        if is_task_complete:
            task_state = TaskState.COMPLETED
            # For completed tasks, the primary output is the artifact.
            # The status message might be minimal or omitted if redundant with the artifact.
            task_status = TaskStatus(state=task_state)
            # Create the final artifact containing both text and data parts
            artifacts.append(Artifact(parts=parts, index=0, append=False))
        elif require_user_input:
            task_state = TaskState.INPUT_REQUIRED
            # For input required, the message contains the agent's question (and potentially partial data)
            message = Message(role="agent", parts=parts)
            task_status = TaskStatus(state=task_state, message=message)
        else:  # Agent is just providing an update without finishing or needing input
            task_state = TaskState.WORKING
            message = Message(role="agent", parts=parts)
            task_status = TaskStatus(state=task_state, message=message)

        return task_status, artifacts

    async def _run_streaming_agent(self, request: SendTaskStreamingRequest):
        task_send_params: TaskSendParams = request.params
        query = self._get_user_query(task_send_params)

        try:
            initial_status = TaskStatus(
                state=TaskState.WORKING,
                message=Message(
                    role="agent", parts=[TextPart(text="Analyzing your text...")]
                ),
            )
            await self.update_store(task_send_params.id, initial_status, [])
            await self.enqueue_events_for_sse(
                task_send_params.id,
                TaskStatusUpdateEvent(
                    id=task_send_params.id, status=initial_status, final=False
                ),
            )

            agent_outcome = await self.agent.invoke(query, task_send_params.sessionId)

            final_task_status, final_artifacts = self._parse_agent_outcome(
                agent_outcome
            )

            latest_task = await self.update_store(
                task_send_params.id,
                final_task_status,
                final_artifacts,
            )
            await self.send_task_notification(latest_task)

            # Enqueue artifact events first (if any)
            for artifact in final_artifacts:
                await self.enqueue_events_for_sse(
                    task_send_params.id,
                    TaskArtifactUpdateEvent(id=task_send_params.id, artifact=artifact),
                )

            # Enqueue the final status update event (marking stream end)
            await self.enqueue_events_for_sse(
                task_send_params.id,
                TaskStatusUpdateEvent(
                    id=task_send_params.id, status=final_task_status, final=True
                ),
            )

        except Exception as e:
            logger.error(
                f"Error during streaming agent execution: {e}\n{traceback.format_exc()}"
            )
            fail_status = TaskStatus(
                state=TaskState.FAILED,
                message=Message(
                    role="agent",
                    parts=[TextPart(text=f"An internal error occurred: {e}")],
                ),
            )
            failed_task = None
            try:
                await self.update_store(task_send_params.id, fail_status, [])
                failed_task = await self.get_task(task_send_params.id)  # type: ignore
            except Exception as update_err:
                logger.error(
                    f"Failed to update task store to FAILED state: {update_err}"
                )

            if failed_task:
                await self.send_task_notification(failed_task)

            await self.enqueue_events_for_sse(
                task_send_params.id,
                InternalError(message=f"An error occurred during agent execution: {e}"),
            )
            await self.enqueue_events_for_sse(
                task_send_params.id,
                TaskStatusUpdateEvent(
                    id=task_send_params.id, status=fail_status, final=True
                ),
            )

    def _validate_request(
        self, request: SendTaskRequest | SendTaskStreamingRequest
    ) -> JSONRPCResponse | None:
        task_send_params: TaskSendParams = request.params
        if task_send_params.acceptedOutputModes and not utils.are_modalities_compatible(
            task_send_params.acceptedOutputModes, ExtractorAgent.SUPPORTED_CONTENT_TYPES
        ):
            logger.warning(
                "Unsupported output mode. Received %s, Support %s",
                task_send_params.acceptedOutputModes,
                ExtractorAgent.SUPPORTED_CONTENT_TYPES,
            )
            return utils.new_incompatible_types_error(request.id)

        if (
            task_send_params.pushNotification
            and not task_send_params.pushNotification.url
        ):
            logger.warning("Push notification URL is missing")
            return JSONRPCResponse(
                id=request.id,
                error=InvalidParamsError(message="Push notification URL is missing"),
            )

        return None

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
                        message="Push notification URL is invalid"
                    ),
                )

        await self.upsert_task(request.params)
        task = await self.update_store(
            request.params.id, TaskStatus(state=TaskState.WORKING), []
        )
        await self.send_task_notification(task)

        task_send_params: TaskSendParams = request.params
        query = self._get_user_query(task_send_params)
        try:
            agent_response = await self.agent.invoke(query, task_send_params.sessionId)
        except Exception as e:
            logger.error(f"Error invoking agent: {e}")
            raise ValueError(f"Error invoking agent: {e}")

        return await self._process_agent_response(request, agent_response)

    async def on_send_task_subscribe(
        self, request: SendTaskStreamingRequest
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        try:
            if error := self._validate_request(request):
                return error

            await self.upsert_task(request.params)

            if request.params.pushNotification:
                if not await self.set_push_notification_info(
                    request.params.id, request.params.pushNotification
                ):
                    return JSONRPCResponse(
                        id=request.id,
                        error=InvalidParamsError(
                            message="Push notification URL is invalid"
                        ),
                    )

            task_send_params: TaskSendParams = request.params
            sse_event_queue = await self.setup_sse_consumer(task_send_params.id, False)

            asyncio.create_task(self._run_streaming_agent(request))

            return self.dequeue_events_for_sse(  # type: ignore
                request.id, task_send_params.id, sse_event_queue
            )
        except Exception as e:
            logger.error(f"Error in SSE stream setup/dequeuing: {e}")
            print(traceback.format_exc())
            return JSONRPCResponse(
                id=request.id,
                error=InternalError(
                    message="An error occurred while streaming the response"
                ),
            )

    async def _process_agent_response(
        self, request: SendTaskRequest, agent_response: dict[str, Any]
    ) -> SendTaskResponse:
        """Processes the agent's response and updates the task store."""
        task_send_params: TaskSendParams = request.params
        task_id = task_send_params.id
        history_length = task_send_params.historyLength

        task_status, artifacts = self._parse_agent_outcome(agent_response)

        task = await self.update_store(task_id, task_status, artifacts)
        task_result = self.append_task_history(task, history_length)
        await self.send_task_notification(task)
        return SendTaskResponse(id=request.id, result=task_result)

    def _get_user_query(self, task_send_params: TaskSendParams) -> str:
        part = task_send_params.message.parts[0]
        if not isinstance(part, TextPart):
            raise ValueError("Only text parts are supported")
        return part.text

    async def send_task_notification(self, task: Task):
        if not await self.has_push_notification_info(task.id):
            logger.info(f"No push notification info found for task {task.id}")
            return
        push_info = await self.get_push_notification_info(task.id)

        logger.info(f"Notifying for task {task.id} => {task.status.state}")
        await self.notification_sender_auth.send_push_notification(
            push_info.url, data=task.model_dump(exclude_none=True)
        )

    async def on_resubscribe_to_task(
        self, request
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        task_id_params: TaskIdParams = request.params
        try:
            sse_event_queue = await self.setup_sse_consumer(task_id_params.id, True)
            return self.dequeue_events_for_sse(  # type: ignore
                request.id, task_id_params.id, sse_event_queue
            )
        except Exception as e:
            logger.error(f"Error while reconnecting to SSE stream: {e}")
            return JSONRPCResponse(
                id=request.id,
                error=InternalError(
                    message=f"An error occurred while reconnecting to stream: {e}"
                ),
            )

    async def set_push_notification_info(
        self, task_id: str, push_notification_config: PushNotificationConfig
    ):
        if not await self.notification_sender_auth.verify_push_notification_url(
            push_notification_config.url
        ):
            return False

        await super().set_push_notification_info(task_id, push_notification_config)
        return True
