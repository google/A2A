# FILE: pocketflow_a2a_agent/task_manager.py
import logging

from collections.abc import AsyncIterable

import pocketflow_a2a.a2a_common.server.utils as server_utils


# Import from the common code you copied
from pocketflow_a2a.a2a_common.server.task_manager import InMemoryTaskManager
from pocketflow_a2a.a2a_common.types import (
    Artifact,
    InternalError,
    InvalidParamsError,
    JSONRPCResponse,
    Message,
    SendTaskRequest,
    SendTaskResponse,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    TaskSendParams,
    TaskState,
    TaskStatus,
    TextPart,
    UnsupportedOperationError,
)

# Import directly from your original PocketFlow files
from .flow import create_agent_flow


logger = logging.getLogger(__name__)


class PocketFlowTaskManager(InMemoryTaskManager):
    """TaskManager implementation that runs the PocketFlow agent."""

    SUPPORTED_CONTENT_TYPES = [
        'text',
        'text/plain',
    ]  # Define what the agent accepts/outputs

    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """Handles non-streaming task requests."""
        logger.info(f'Received task send request: {request.params.id}')

        # Validate output modes
        if not server_utils.are_modalities_compatible(
            request.params.acceptedOutputModes, self.SUPPORTED_CONTENT_TYPES
        ):
            logger.warning(
                'Unsupported output mode. Received %s, Support %s',
                request.params.acceptedOutputModes,
                self.SUPPORTED_CONTENT_TYPES,
            )
            return SendTaskResponse(
                id=request.id,
                error=server_utils.new_incompatible_types_error(
                    request.id
                ).error,
            )

        # Upsert the task in the store (initial state: submitted)
        # We create the task first so its state can be tracked,
        # even if the sync execution fails
        await self.upsert_task(request.params)
        # Update state to working before running
        await self.update_store(
            request.params.id, TaskStatus(state=TaskState.WORKING), []
        )

        # --- Run the PocketFlow logic ---
        task_params: TaskSendParams = request.params
        query = self._get_user_query(task_params)
        if query is None:
            fail_status = TaskStatus(
                state=TaskState.FAILED,
                message=Message(
                    role='agent', parts=[TextPart(text='No text query found')]
                ),
            )
            await self.update_store(task_params.id, fail_status, [])
            return SendTaskResponse(
                id=request.id,
                error=InvalidParamsError(
                    message='No text query found in message parts'
                ),
            )

        shared_data = {'question': query}
        agent_flow = create_agent_flow()  # Create the flow instance

        try:
            # Run the synchronous PocketFlow
            # In a real async server, you might run this in a separate thread/process
            # executor to avoid blocking the event loop.
            # For simplicity here, we run it directly.
            # Consider adding a timeout if flows can hang.
            logger.info(f'Running PocketFlow for task {task_params.id}...')
            agent_flow.run(
                shared_data
            )  # Run the flow, modifying shared_data in place
            logger.info(f'PocketFlow completed for task {task_params.id}')
            # Access the original shared_data dictionary, which was modified by the flow
            answer_text = shared_data.get(
                'answer', 'Agent did not produce a final answer text.'
            )

            # --- Package result into A2A Task ---
            final_task_status = TaskStatus(state=TaskState.COMPLETED)
            # Package the answer as an artifact
            final_artifact = Artifact(parts=[TextPart(text=answer_text)])

            # Update the task in the store with final status and artifact
            final_task = await self.update_store(
                task_params.id, final_task_status, [final_artifact]
            )

            # Prepare and return the A2A response
            task_result = self.append_task_history(
                final_task, task_params.historyLength
            )
            return SendTaskResponse(id=request.id, result=task_result)

        except Exception as e:
            logger.error(
                f'Error executing PocketFlow for task {task_params.id}: {e}',
                exc_info=True,
            )
            # Update task state to FAILED
            fail_status = TaskStatus(
                state=TaskState.FAILED,
                message=Message(
                    role='agent',
                    parts=[TextPart(text=f'Agent execution failed: {e}')],
                ),
            )
            await self.update_store(task_params.id, fail_status, [])
            return SendTaskResponse(
                id=request.id, error=InternalError(message=f'Agent error: {e}')
            )

    async def on_send_task_subscribe(
        self, request: SendTaskStreamingRequest
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        """Handles streaming requests - Not implemented for this synchronous agent."""
        logger.warning(
            f'Streaming requested for task {request.params.id}, but not supported by this PocketFlow agent implementation.'  # noqa: E501
        )
        # Return an error indicating streaming is not supported
        return JSONRPCResponse(
            id=request.id,
            error=UnsupportedOperationError(
                message='Streaming not supported by this agent'
            ),
        )

    def _get_user_query(self, task_send_params: TaskSendParams) -> str | None:
        """Extracts the first text part from the user message."""
        if not task_send_params.message or not task_send_params.message.parts:
            logger.warning(
                f'No message parts found for task {task_send_params.id}'
            )
            return None
        for part in task_send_params.message.parts:
            # Ensure part is treated as a dictionary if it came from JSON
            part_dict = part if isinstance(part, dict) else part.model_dump()
            if part_dict.get('type') == 'text' and 'text' in part_dict:
                return part_dict['text']
        logger.warning(
            f'No text part found in message for task {task_send_params.id}'
        )
        return None  # No text part found
