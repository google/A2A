import json
import logging
import re  # Import regex
import uuid
from abc import ABC, abstractmethod
from collections.abc import AsyncIterable
from typing import Any, Union

from common.server import utils
from common.server.task_manager import InMemoryTaskManager
from common.types import FileContent  # Import FileContent
from common.types import TextPart  # Import TextPart
from common.types import (Artifact, FilePart, InternalError, JSONRPCResponse,
                          Message, MessageSendParams, Part, SendMessageRequest,
                          SendMessageResponse, SendMessageStreamRequest,
                          SendMessageStreamResponse, Task,
                          TaskArtifactUpdateEvent, TaskState, TaskStatus,
                          TaskStatusUpdateEvent)
from google.genai import types as genai_types  # Renamed to avoid conflict

logger = logging.getLogger(__name__)


class AgentWithTaskManager(ABC):
    @abstractmethod
    def get_processing_message(self) -> str:
        pass

    def invoke(self, query, session_id) -> str:
        session = self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id
        )
        content = genai_types.Content(
            role='user', parts=[genai_types.Part.from_text(text=query)]
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
            session_id=session_id
        )
        content = genai_types.Content(
            role='user', parts=[genai_types.Part.from_text(text=query)]
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

    def _validate_request(
        self,
        request: SendMessageRequest | SendMessageStreamRequest,
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

            last_processed_task_state = None
            async for item in self.agent.stream(query, contextId):
                is_task_complete = item['is_task_complete']
                artifacts = None
                current_event_message_parts: list[Part] 
                current_progress_percent: Optional[int] = item.get('progress_percent')

                if not is_task_complete:
                    task_state = TaskState.WORKING
                    current_event_message_parts = [TextPart(type='text', text=item['updates'])]
                else:
                    # For video agent, 'content' is the GCS URL string.
                    # 'artifact_name', 'artifact_description', 'final_message_text' are also expected.
                    final_message_text = item.get('final_message_text', "Video generation complete.")
                    file_part_data = item.get('file_part_data') # Check for file part data

                    current_event_message_parts = [TextPart(type='text', text=final_message_text)] 
                    
                    artifacts = []
                    if file_part_data:
                        # Create a File Part for the artifact using the structured data from the agent
                        try:
                            file_content_obj = FileContent(**file_part_data) # Create FileContent from data
                            # Log the created FileContent object to verify its attributes
                            logger.debug(f"Created FileContent object: uri='{file_content_obj.uri}', mimeType='{getattr(file_content_obj, 'mimeType', 'N/A')}', bytes_present={file_content_obj.bytes is not None}")
                            file_part_obj = FilePart(type='file', file=file_content_obj) # Create FilePart
                            artifacts.append(Artifact(
                                name=item.get('artifact_name', 'generated_video.mp4'), # Use .mp4 extension
                                description=item.get('artifact_description', 'Generated video'),
                                parts=[file_part_obj], # Artifact contains the file part
                                index=0,
                                append=False
                            ))
                            task_state = TaskState.COMPLETED
                        except Exception as artifact_e:
                             logger.error(f"Failed to create file artifact part from data {file_part_data}: {artifact_e}")
                             # Fallback to text artifact with URL if video part creation fails
                             artifacts.append(Artifact(
                                name=item.get('artifact_name', 'generated_video_link.txt'), 
                                description=item.get('artifact_description', 'Link to generated video (error creating video part)'),
                                parts=[TextPart(type='text', text=file_part_data.get('uri', 'URI not available'))],
                                index=0, append=False
                             ))
                             task_state = TaskState.COMPLETED 
                    else: 
                        task_state = TaskState.FAILED
                        if 'content' in item and isinstance(item['content'], str):
                            current_event_message_parts = [TextPart(type='text', text=item['content'])]

                
                # Create message and task status for the current update
                current_message = Message(
                    role='agent',
                    parts=current_event_message_parts, 
                    messageId=str(uuid.uuid4()),
                    taskId=taskId,
                    contextId=contextId,
                )
                current_task_status = TaskStatus(
                    state=task_state,
                    message=current_message,
                    progress=current_progress_percent 
                )
                
                await self._update_store(taskId, current_task_status, artifacts if is_task_complete else None)

                last_processed_task_state = task_state # Keep track of the latest state

                status_update_to_yield = TaskStatusUpdateEvent(
                    id=taskId,
                    contextId=contextId,
                    status=current_task_status, # Send the full status including the message
                    final=False, 
                )
                logger.info(f"TASK_MANAGER SENDING TO CLIENT (TaskStatusUpdateEvent, final=False): {status_update_to_yield.model_dump_json(indent=2)}")
                yield SendMessageStreamResponse(id=request.id, result=status_update_to_yield)

                # If there are artifacts with this update (typically on completion), yield them
                if artifacts:
                    for artifact_item in artifacts:
                        yield SendMessageStreamResponse(
                            id=request.id,
                            result=TaskArtifactUpdateEvent(
                                id=taskId,
                                contextId=contextId,
                                artifact=artifact_item,
                            ),
                        )
                        # Log the TaskArtifactUpdateEvent without the raw bytes from FileContent
                        event_for_logging = TaskArtifactUpdateEvent(id=taskId, contextId=contextId, artifact=artifact_item)
                        json_to_log = event_for_logging.model_dump_json(
                            indent=2,
                            exclude={'artifact': {'parts': {
                                '__all__': {'file': {'bytes': True}}}}}
                        )
                        logger.debug(f"TASK_MANAGER SENDING TO CLIENT (TaskArtifactUpdateEvent): {json_to_log}")
                
                if is_task_complete:
                    break
            
            if last_processed_task_state is not None:
                final_status_update = TaskStatusUpdateEvent(
                        id=taskId,
                        contextId=contextId,
                        status=TaskStatus(state=last_processed_task_state), # Minimal status for final event
                        final=True,
                    )
                logger.info(f"TASK_MANAGER SENDING TO CLIENT (TaskStatusUpdateEvent, final=True): {final_status_update.model_dump_json(indent=2)}")
                yield SendMessageStreamResponse(
                    id=request.id,
                    result=final_status_update,
                )
        except Exception as e:
            logger.error(f'An error occurred while streaming the response: {e}')
            yield JSONRPCResponse(
                id=request.id,
                error=InternalError(
                    message=f'An error occurred while streaming the response {e}'
                ),
            )

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

        message_parts_for_invoke = [TextPart(type='text', text=result)]
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
                    parts=message_parts_for_invoke,
                    contextId=contextId,
                    messageId=str(uuid.uuid4()),
                    taskId=taskId,
                )
                if task_state == TaskState.INPUT_REQUIRED
                else None,
            ),
            [Artifact(parts=message_parts_for_invoke)]
            if task_state == TaskState.COMPLETED
            else [],
        )
        return SendMessageResponse(id=request.id, result=task)
