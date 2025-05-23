import base64
import datetime
import json
import os
import uuid

from typing import Optional, Tuple

import httpx

from a2a.types import (
    AgentCard,
    Artifact,
    DataPart,
    FilePart,
    FileWithBytes,
    FileWithUri,
    Message,
    Part,
    Role,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)
from google.adk import Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.events.event import Event as ADKEvent
from google.adk.events.event_actions import EventActions as ADKEventActions
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
from hosts.multiagent.host_agent import HostAgent
from hosts.multiagent.remote_agent_connection import (
    TaskCallbackArg,
)
from utils.agent_card import get_agent_card

from service.server.application_manager import ApplicationManager
from service.types import Conversation, Event


class ADKHostManager(ApplicationManager):
    """An implementation of memory based management with fake agent actions

    This implements the interface of the ApplicationManager to plug into
    the AgentServer. This acts as the service contract that the Mesop app
    uses to send messages to the agent and provide information for the frontend.
    """

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        api_key: str = '',
        uses_vertex_ai: bool = False,
    ):
        self._conversations: list[Conversation] = []
        self._messages: list[Message] = []
        self._tasks: list[Task] = []
        self._events: dict[str, Event] = {}
        self._pending_message_ids: list[str] = []
        self._agents: list[AgentCard] = []
        self._artifact_chunks: dict[str, list[Artifact]] = {}
        self._session_service = InMemorySessionService()
        self._artifact_service = InMemoryArtifactService()
        self._memory_service = InMemoryMemoryService()
        self._host_agent = HostAgent([], http_client, self.task_callback)
        self._context_to_conversation: dict[str, str] = {}
        self.user_id = 'test_user'
        self.app_name = 'A2A'
        self.api_key = api_key or os.environ.get('GOOGLE_API_KEY', '')
        self.uses_vertex_ai = (
            uses_vertex_ai
            or os.environ.get('GOOGLE_GENAI_USE_VERTEXAI', '').upper() == 'TRUE'
        )

        # Set environment variables based on auth method
        if self.uses_vertex_ai:
            os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'TRUE'

        elif self.api_key:
            # Use API key authentication
            os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'FALSE'
            os.environ['GOOGLE_API_KEY'] = self.api_key

        self._initialize_host()

        # Map of message id to task id
        self._task_map: dict[str, str] = {}
        # Map to manage 'lost' message ids until protocol level id is introduced
        self._next_id: dict[
            str, str
        ] = {}  # dict[str, str]: previous message to next message

    def _initialize_host(self):
        agent = self._host_agent.create_agent()
        self._host_runner = Runner(
            app_name=self.app_name,
            agent=agent,
            artifact_service=self._artifact_service,
            session_service=self._session_service,
            memory_service=self._memory_service,
        )

    async def create_conversation(self) -> Conversation:
        session = await self._session_service.create_session(
            app_name=self.app_name, user_id=self.user_id
        )
        conversation_id = session.id
        c = Conversation(conversation_id=conversation_id, is_active=True)
        self._conversations.append(c)
        return c

    def update_api_key(self, api_key: str):
        """Update the API key and reinitialize the host if needed"""
        if api_key and api_key != self.api_key:
            self.api_key = api_key

            # Only update if not using Vertex AI
            if not self.uses_vertex_ai:
                os.environ['GOOGLE_API_KEY'] = api_key
                # Reinitialize host with new API key
                self._initialize_host()

                # Map of message id to task id
                self._task_map = {}

    def sanitize_message(self, message: Message) -> Message:
        if message.contextId:
            conversation = self.get_conversation(message.contextId)
            if not conversation:
                return message
            # Check if the last event in the conversation was tied to a task.
            if conversation.messages:
                task_id = conversation.messages[-1].taskId
                if task_id and task_still_open(
                    next(
                        filter(lambda x: x and x.id == task_id, self._tasks),
                        None,
                    )
                ):
                    message.taskId = task_id
        return message

    async def process_message(self, message: Message):
        message_id = message.messageId
        if message_id:
            self._pending_message_ids.append(message_id)
        context_id = message.contextId
        conversation = self.get_conversation(context_id)
        self._messages.append(message)
        if conversation:
            conversation.messages.append(message)
        self.add_event(
            Event(
                id=str(uuid.uuid4()),
                actor='user',
                content=message,
                timestamp=datetime.datetime.utcnow().timestamp(),
            )
        )
        final_event = None
        # Determine if a task is to be resumed.
        session = await self._session_service.get_session(
            app_name='A2A', user_id='test_user', session_id=context_id
        )
        task_id = message.taskId
        # Update state must happen in an event
        state_update = {
            'task_id': task_id,
            'context_id': context_id,
            'message_id': message.messageId,
        }
        # Need to upsert session state now, only way is to append an event.
        await self._session_service.append_event(
            session,
            ADKEvent(
                id=ADKEvent.new_id(),
                author='host_agent',
                invocation_id=ADKEvent.new_id(),
                actions=ADKEventActions(state_delta=state_update),
            ),
        )
        async for event in self._host_runner.run_async(
            user_id=self.user_id,
            session_id=context_id,
            new_message=self.adk_content_from_message(message),
        ):
            if (
                event.actions.state_delta
                and 'task_id' in event.actions.state_delta
            ):
                task_id = event.actions.state_delta['task_id']
            self.add_event(
                Event(
                    id=event.id,
                    actor=event.author,
                    content=await self.adk_content_to_message(
                        event.content, context_id, task_id
                    ),
                    timestamp=event.timestamp,
                )
            )
            final_event = event
        response: Message | None = None
        if final_event:
            if (
                final_event.actions.state_delta
                and 'task_id' in final_event.actions.state_delta
            ):
                task_id = event.actions.state_delta['task_id']
            final_event.content.role = 'model'
            response = await self.adk_content_to_message(
                final_event.content, context_id, task_id
            )
            self._messages.append(response)

        if conversation and response:
            conversation.messages.append(response)
        self._pending_message_ids.remove(message_id)

    def add_task(self, task: Task):
        self._tasks.append(task)

    def update_task(self, task: Task):
        for i, t in enumerate(self._tasks):
            if t.id == task.id:
                self._tasks[i] = task
                return

    def task_callback(self, task: TaskCallbackArg, agent_card: AgentCard):
        self.emit_event(task, agent_card)
        if isinstance(task, TaskStatusUpdateEvent):
            current_task = self.add_or_get_task(task)
            current_task.status = task.status
            self.attach_message_to_task(task.status.message, current_task.id)
            self.insert_message_history(current_task, task.status.message)
            self.update_task(current_task)
            return current_task
        elif isinstance(task, TaskArtifactUpdateEvent):
            current_task = self.add_or_get_task(task)
            self.process_artifact_event(current_task, task)
            self.update_task(current_task)
            return current_task
        # Otherwise this is a Task, either new or updated
        elif not any(filter(lambda x: x and x.id == task.id, self._tasks)):
            self.attach_message_to_task(task.status.message, task.id)
            self.add_task(task)
            return task
        else:
            self.attach_message_to_task(task.status.message, task.id)
            self.update_task(task)
            return task

    def emit_event(self, task: TaskCallbackArg, agent_card: AgentCard):
        content = None
        context_id = task.contextId
        if isinstance(task, TaskStatusUpdateEvent):
            if task.status.message:
                content = task.status.message
            else:
                content = Message(
                    parts=[Part(root=TextPart(text=str(task.status.state)))],
                    role=Role.agent,
                    messageId=str(uuid.uuid4()),
                    contextId=context_id,
                    taskId=task.taskId,
                )
        elif isinstance(task, TaskArtifactUpdateEvent):
            content = Message(
                parts=task.artifact.parts,
                role=Role.agent,
                messageId=str(uuid.uuid4()),
                contextId=context_id,
                taskId=task.taskId,
            )
        elif task.status and task.status.message:
            content = task.status.message
        elif task.artifacts:
            parts = []
            for a in task.artifacts:
                parts.extend(a.parts)
            content = Message(
                parts=parts,
                role=Role.agent,
                messageId=str(uuid.uuid4()),
                taskId=task.id,
                contextId=context_id,
            )
        else:
            content = Message(
                parts=[Part(root=TextPart(text=str(task.status.state)))],
                role=Role.agent,
                messageId=str(uuid.uuid4()),
                taskId=task.id,
                contextId=context_id,
            )
        if content:
            self.add_event(
                Event(
                    id=str(uuid.uuid4()),
                    actor=agent_card.name,
                    content=content,
                    timestamp=datetime.datetime.utcnow().timestamp(),
                )
            )

    def attach_message_to_task(self, message: Message | None, task_id: str):
        if message:
            self._task_map[message.messageId] = task_id

    def insert_message_history(self, task: Task, message: Message | None):
        if not message:
            return
        if task.history is None:
            task.history = []
        message_id = message.messageId
        if not message_id:
            return
        if task.history and (
            task.status.message
            and task.status.message.messageId
            not in [x.messageId for x in task.history]
        ):
            task.history.append(task.status.message)
        elif not task.history and task.status.message:
            task.history = [task.status.message]
        else:
            print(
                'Message id already in history',
                task.status.message.messageId if task.status.message else '',
                task.history,
            )

    def add_or_get_task(self, event: TaskCallbackArg):
        task_id = None
        if isinstance(event, Message):
            task_id = event.taskId
        elif isinstance(event, Task):
            task_id = event.id
        else:
            task_id = event.taskId
        if not task_id:
            task_id = str(uuid.uuid4())
        current_task = next(
            filter(lambda x: x.id == task_id, self._tasks), None
        )
        if not current_task:
            context_id = event.contextId
            current_task = Task(
                id=task_id,
                # initialize with submitted
                status=TaskStatus(state=TaskState.submitted),
                artifacts=[],
                contextId=context_id,
            )
            self.add_task(current_task)
            return current_task

        return current_task

    def process_artifact_event(
        self, current_task: Task, task_update_event: TaskArtifactUpdateEvent
    ):
        artifact = task_update_event.artifact
        if not task_update_event.append:
            # received the first chunk or entire payload for an artifact
            if (
                task_update_event.lastChunk is None
                or task_update_event.lastChunk
            ):
                # lastChunk bit is missing or is set to true, so this is the entire payload
                # add this to artifacts
                if not current_task.artifacts:
                    current_task.artifacts = []
                current_task.artifacts.append(artifact)
            else:
                # this is a chunk of an artifact, stash it in temp store for assembling
                if artifact.artifactId not in self._artifact_chunks:
                    self._artifact_chunks[artifact.artifactId] = []
                self._artifact_chunks[artifact.artifactId].append(artifact)
        else:
            # we received an append chunk, add to the existing temp artifact
            current_temp_artifact = self._artifact_chunks[artifact.artifactId][
                -1
            ]
            # TODO handle if current_temp_artifact is missing
            current_temp_artifact.parts.extend(artifact.parts)
            if task_update_event.lastChunk:
                if current_task.artifacts:
                    current_task.artifacts.append(current_temp_artifact)
                else:
                    current_task.artifacts = [current_temp_artifact]
                del self._artifact_chunks[artifact.artifactId][-1]

    def add_event(self, event: Event):
        self._events[event.id] = event

    def get_conversation(
        self, conversation_id: Optional[str]
    ) -> Optional[Conversation]:
        if not conversation_id:
            return None
        return next(
            filter(
                lambda c: c and c.conversation_id == conversation_id,
                self._conversations,
            ),
            None,
        )

    def get_pending_messages(self) -> list[tuple[str, str]]:
        rval = []
        for message_id in self._pending_message_ids:
            if message_id in self._task_map:
                task_id = self._task_map[message_id]
                task = next(
                    filter(lambda x: x.id == task_id, self._tasks), None
                )
                if not task:
                    rval.append((message_id, ''))
                elif task.history and task.history[-1].parts:
                    if len(task.history) == 1:
                        rval.append((message_id, 'Working...'))
                    else:
                        part = task.history[-1].parts[0]
                        rval.append(
                            (
                                message_id,
                                part.root.text
                                if part.root.kind == 'text'
                                else 'Working...',
                            )
                        )
            else:
                rval.append((message_id, ''))
        return rval

    def register_agent(self, url):
        agent_data = get_agent_card(url)
        if not agent_data.url:
            agent_data.url = url
        self._agents.append(agent_data)
        self._host_agent.register_agent_card(agent_data)
        # Now update the host agent definition
        self._initialize_host()

    @property
    def agents(self) -> list[AgentCard]:
        return self._agents

    @property
    def conversations(self) -> list[Conversation]:
        return self._conversations

    @property
    def tasks(self) -> list[Task]:
        return self._tasks

    @property
    def events(self) -> list[Event]:
        return sorted(self._events.values(), key=lambda x: x.timestamp)

    def adk_content_from_message(self, message: Message) -> types.Content:
        parts: list[types.Part] = []
        for p in message.parts:
            part = p.root
            if part.kind == 'text':
                parts.append(types.Part.from_text(text=part.text))
            elif part.kind == 'data':
                json_string = json.dumps(part.data)
                parts.append(types.Part.from_text(text=json_string))
            elif part.kind == 'file':
                if isinstance(part.file, FileWithUri):
                    parts.append(
                        types.Part.from_uri(
                            file_uri=part.file.uri,
                            mime_type=part.file.mimeType,
                        )
                    )
                else:
                    parts.append(
                        types.Part.from_bytes(
                            data=part.file.bytes.encode('utf-8'),
                            mime_type=part.file.mimeType,
                        )
                    )
        return types.Content(parts=parts, role=message.role)

    async def adk_content_to_message(
        self,
        content: types.Content,
        context_id: str | None,
        task_id: str | None,
    ) -> Message:
        parts: list[Part] = []
        if not content.parts:
            return Message(
                parts=[],
                role=content.role if content.role == Role.user else Role.agent,
                contextId=context_id,
                taskId=task_id,
                messageId=str(uuid.uuid4()),
            )
        for part in content.parts:
            if part.text:
                # try parse as data
                try:
                    data = json.loads(part.text)
                    parts.append(Part(root=DataPart(data=data)))
                except:
                    parts.append(Part(root=TextPart(text=part.text)))
            elif part.inline_data:
                parts.append(
                    Part(
                        root=FilePart(
                            file=FileWithBytes(
                                bytes=part.inline_data.decode('utf-8'),
                                mimeType=part.file_data.mime_type,
                            ),
                        )
                    )
                )
            elif part.file_data:
                parts.append(
                    Part(
                        root=FilePart(
                            file=FileWithUri(
                                uri=part.file_data.file_uri,
                                mimeType=part.file_data.mime_type,
                            )
                        )
                    )
                )
            # These aren't managed by the A2A message structure, these are internal
            # details of ADK, we will simply flatten these to json representations.
            elif part.video_metadata:
                parts.append(
                    Part(root=DataPart(data=part.video_metadata.model_dump()))
                )
            elif part.thought:
                parts.append(Part(root=TextPart(text='thought')))
            elif part.executable_code:
                parts.append(
                    Part(root=DataPart(data=part.executable_code.model_dump()))
                )
            elif part.function_call:
                parts.append(
                    Part(root=DataPart(data=part.function_call.model_dump()))
                )
            elif part.function_response:
                parts.extend(
                    await self._handle_function_response(
                        part, context_id, task_id
                    )
                )
            else:
                raise ValueError('Unexpected content, unknown type')
        return Message(
            role=content.role if content.role == Role.user else Role.agent,
            parts=parts,
            contextId=context_id,
            taskId=task_id,
            messageId=str(uuid.uuid4()),
        )

    async def _handle_function_response(
        self, part: types.Part, context_id: str | None, task_id: str | None
    ) -> list[Part]:
        parts = []
        try:
            for p in part.function_response.response['result']:
                if isinstance(p, str):
                    parts.append(Part(root=TextPart(text=p)))
                elif isinstance(p, dict):
                    if 'kind' in p and p['kind'] == 'file':
                        parts.append(Part(root=FilePart(**p)))
                    else:
                        parts.append(Part(root=DataPart(data=p)))
                elif isinstance(p, DataPart):
                    if 'artifact-file-id' in p.data:
                        file_part = await self._artifact_service.load_artifact(
                            user_id=self.user_id,
                            session_id=context_id,
                            app_name=self.app_name,
                            filename=p.data['artifact-file-id'],
                        )
                        file_data = file_part.inline_data
                        base64_data = base64.b64encode(file_data.data).decode(
                            'utf-8'
                        )
                        parts.append(
                            Part(
                                root=FilePart(
                                    file=FileWithBytes(
                                        bytes=base64_data,
                                        mimeType=file_data.mime_type,
                                        name='artifact_file',
                                    )
                                )
                            )
                        )
                    else:
                        parts.append(Part(root=DataPart(data=p.data)))
                else:
                    content = Message(
                        parts=[Part(root=TextPart(text='Unknown content'))],
                        role=Role.agent,
                        messageId=str(uuid.uuid4()),
                        taskId=task_id,
                        contextId=context_id,
                    )
        except Exception as e:
            print("Couldn't convert to messages:", e)
            parts.append(
                Part(root=DataPart(data=part.function_response.model_dump()))
            )
        return parts


def get_message_id(m: Message | None) -> str | None:
    if not m or not m.metadata or 'message_id' not in m.metadata:
        return None
    return m.metadata['message_id']


def task_still_open(task: Task | None) -> bool:
    if not task:
        return False
    return task.status.state in [
        TaskState.submitted,
        TaskState.working,
        TaskState.input_required,
    ]
