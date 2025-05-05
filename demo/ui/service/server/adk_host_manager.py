import base64
import datetime
import json
import os
import uuid

from common.types import (
    AgentCard,
    DataPart,
    FileContent,
    FilePart,
    Message,
    Part,
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
from service.server.application_manager import ApplicationManager
from service.types import Conversation, Event
from utils.agent_card import get_agent_card


class ADKHostManager(ApplicationManager):
    """An implementation of memory based management with fake agent actions

    This implements the interface of the ApplicationManager to plug into
    the AgentServer. This acts as the service contract that the Mesop app
    uses to send messages to the agent and provide information for the frontend.
    """

    _conversations: list[Conversation]
    _messages: list[Message]
    _tasks: list[Task]
    _events: dict[str, Event]
    _pending_message_ids: list[str]
    _agents: list[AgentCard]
    _task_map: dict[str, str]

    def __init__(self, api_key: str = '', uses_vertex_ai: bool = False):
        self._conversations = []
        self._messages = []
        self._tasks = []
        self._events = {}
        self._pending_message_ids = []
        self._agents = []
        self._artifact_chunks = {}
        self._session_service = InMemorySessionService()
        self._artifact_service = InMemoryArtifactService()
        self._memory_service = InMemoryMemoryService()
        self._host_agent = HostAgent([], self.task_callback)
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
        self._task_map = {}
        # Map to manage 'lost' message ids until protocol level id is introduced
        self._next_id = {}  # dict[str, str]: previous message to next message

    def update_api_key(self, api_key: str):
        """Update the API key and reinitialize the host if needed"""
        if api_key and api_key != self.api_key:
            self.api_key = api_key

            # Only update if not using Vertex AI
            if not self.uses_vertex_ai:
                os.environ['GOOGLE_API_KEY'] = api_key
                # Reinitialize host with new API key
                self._initialize_host()

    def _initialize_host(self):
        agent = self._host_agent.create_agent()
        self._host_runner = Runner(
            app_name=self.app_name,
            agent=agent,
            artifact_service=self._artifact_service,
            session_service=self._session_service,
            memory_service=self._memory_service,
        )

    def create_conversation(self) -> Conversation:
        session = self._session_service.create_session(
            app_name=self.app_name, user_id=self.user_id
        )
        conversation_id = session.id
        c = Conversation(conversation_id=conversation_id, is_active=True)
        self._conversations.append(c)
        return c

    def sanitize_message(self, message: Message) -> Message:
        if not message.metadata:
            message.metadata = {}
        if 'message_id' not in message.metadata:
            message.metadata.update({'message_id': str(uuid.uuid4())})
        if 'conversation_id' in message.metadata:
            conversation = self.get_conversation(
                message.metadata['conversation_id']
            )
            if conversation:
                if conversation.messages:
                    # Get the last message
                    last_message_id = get_message_id(conversation.messages[-1])
                    if last_message_id:
                        message.metadata.update(
                            {'last_message_id': last_message_id}
                        )
        return message

    async def process_message(self, message: Message):
        self._messages.append(message)
        message_id = get_message_id(message)
        if message_id:
            self._pending_message_ids.append(message_id)
        conversation_id = (
            message.metadata['conversation_id']
            if 'conversation_id' in message.metadata
            else None
        )
        # Now check the conversation and attach the message id.
        conversation = self.get_conversation(conversation_id)
        if conversation:
            conversation.messages.append(message)
        self.add_event(
            Event(
                id=str(uuid.uuid4()),
                actor='user',
                content=message,
                timestamp=datetime.datetime.now(datetime.UTC).timestamp(),
            )
        )
        final_event: GenAIEvent | None = None
        # Determine if a task is to be resumed.
        session = self._session_service.get_session(
            app_name='A2A', user_id='test_user', session_id=conversation_id
        )
        # Update state must happen in the event
        state_update = {
            'input_message_metadata': message.metadata,
            'session_id': conversation_id,
        }
        last_message_id = get_last_message_id(message)
        if (
            last_message_id
            and last_message_id in self._task_map
            and task_still_open(
                next(
                    filter(
                        lambda x: x.id == self._task_map[last_message_id],
                        self._tasks,
                    ),
                    None,
                )
            )
        ):
            state_update['task_id'] = self._task_map[last_message_id]
        # Need to upsert session state now, only way is to append an event.
        self._session_service.append_event(
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
            session_id=conversation_id,
            new_message=self.adk_content_from_message(message),
        ):
            self.add_event(
                Event(
                    id=event.id,
                    actor=event.author,
                    content=self.adk_content_to_message(
                        event.content, conversation_id
                    ),
                    timestamp=event.timestamp,
                )
            )
            final_event = event
        response: Message | None = None
        if final_event:
            final_event.content.role = 'model'
            response = self.adk_content_to_message(
                final_event.content, conversation_id
            )
            last_message_id = get_message_id(message)
            new_message_id = ''
            if last_message_id and last_message_id in self._next_id:
                new_message_id = self._next_id[last_message_id]
            else:
                new_message_id = str(uuid.uuid4())
                last_message_id = None
            response.metadata = {
                **message.metadata,
                'last_message_id': last_message_id,
                'message_id': new_message_id,
            }
            self._messages.append(response)

        if conversation:
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
            self.insert_id_trace(task.status.message)
            return current_task
        if isinstance(task, TaskArtifactUpdateEvent):
            current_task = self.add_or_get_task(task)
            self.process_artifact_event(current_task, task)
            self.update_task(current_task)
            return current_task
        # Otherwise this is a Task, either new or updated
        if not any(filter(lambda x: x.id == task.id, self._tasks)):
            self.attach_message_to_task(task.status.message, task.id)
            self.insert_id_trace(task.status.message)
            self.add_task(task)
            return task
        self.attach_message_to_task(task.status.message, task.id)
        self.insert_id_trace(task.status.message)
        self.update_task(task)
        return task

    def emit_event(self, task: TaskCallbackArg, agent_card: AgentCard):
        content = None
        conversation_id = get_conversation_id(task)
        metadata = (
            {'conversation_id': conversation_id} if conversation_id else None
        )
        if isinstance(task, TaskStatusUpdateEvent):
            if task.status.message:
                content = task.status.message
            else:
                content = Message(
                    parts=[TextPart(text=str(task.status.state))],
                    role='agent',
                    metadata=metadata,
                )
        elif isinstance(task, TaskArtifactUpdateEvent):
            content = Message(
                parts=task.artifact.parts,
                role='agent',
                metadata=metadata,
            )
        elif task.status and task.status.message:
            content = task.status.message
        elif task.artifacts:
            parts = []
            for a in task.artifacts:
                parts.extend(a.parts)
            content = Message(
                parts=parts,
                role='agent',
                metadata=metadata,
            )
        else:
            content = Message(
                parts=[TextPart(text=str(task.status.state))],
                role='agent',
                metadata=metadata,
            )
        self.add_event(
            Event(
                id=str(uuid.uuid4()),
                actor=agent_card.name,
                content=content,
                timestamp=datetime.datetime.now(datetime.UTC).timestamp(),
            )
        )

    def attach_message_to_task(self, message: Message | None, task_id: str):
        if message and message.metadata and 'message_id' in message.metadata:
            self._task_map[message.metadata['message_id']] = task_id

    def insert_id_trace(self, message: Message | None):
        if not message:
            return
        message_id = get_message_id(message)
        last_message_id = get_last_message_id(message)
        if message_id and last_message_id:
            self._next_id[last_message_id] = message_id

    def insert_message_history(self, task: Task, message: Message | None):
        if not message:
            return
        if task.history is None:
            task.history = []
        message_id = get_message_id(message)
        if not message_id:
            return
        if get_message_id(task.status.message) not in [
            get_message_id(x) for x in task.history
        ]:
            task.history.append(task.status.message)
        else:
            print(
                'Message id already in history',
                get_message_id(task.status.message),
                task.history,
            )

    def add_or_get_task(self, task: TaskCallbackArg):
        current_task = next(
            filter(lambda x: x.id == task.id, self._tasks), None
        )
        if not current_task:
            conversation_id = None
            if task.metadata and 'conversation_id' in task.metadata:
                conversation_id = task.metadata['conversation_id']
            current_task = Task(
                id=task.id,
                status=TaskStatus(
                    state=TaskState.SUBMITTED
                ),  # initialize with submitted
                metadata=task.metadata,
                artifacts=[],
                sessionId=conversation_id,
            )
            self.add_task(current_task)
            return current_task

        return current_task

    def process_artifact_event(
        self, current_task: Task, task_update_event: TaskArtifactUpdateEvent
    ):
        artifact = task_update_event.artifact
        if not artifact.append:
            # received the first chunk or entire payload for an artifact
            if artifact.lastChunk is None or artifact.lastChunk:
                # lastChunk bit is missing or is set to true, so this is the entire payload
                # add this to artifacts
                if not current_task.artifacts:
                    current_task.artifacts = []
                current_task.artifacts.append(artifact)
            else:
                # this is a chunk of an artifact, stash it in temp store for assembling
                if task_update_event.id not in self._artifact_chunks:
                    self._artifact_chunks[task_update_event.id] = {}
                self._artifact_chunks[task_update_event.id][artifact.index] = (
                    artifact
                )
        else:
            # we received an append chunk, add to the existing temp artifact
            current_temp_artifact = self._artifact_chunks[task_update_event.id][
                artifact.index
            ]
            # TODO handle if current_temp_artifact is missing
            current_temp_artifact.parts.extend(artifact.parts)
            if artifact.lastChunk:
                current_task.artifacts.append(current_temp_artifact)
                del self._artifact_chunks[task_update_event.id][artifact.index]

    def add_event(self, event: Event):
        self._events[event.id] = event

    def get_conversation(
        self, conversation_id: str | None
    ) -> Conversation | None:
        if not conversation_id:
            return None
        return next(
            filter(
                lambda c: c.conversation_id == conversation_id,
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
                                part.text
                                if part.type == 'text'
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
        for part in message.parts:
            if part.type == 'text':
                parts.append(types.Part.from_text(text=part.text))
            elif part.type == 'data':
                json_string = json.dumps(part.data)
                parts.append(types.Part.from_text(text=json_string))
            elif part.type == 'file':
                if part.uri:
                    parts.append(
                        types.Part.from_uri(
                            file_uri=part.uri, mime_type=part.mimeType
                        )
                    )
                elif content_part.bytes:
                    parts.append(
                        types.Part.from_bytes(
                            data=part.bytes.encode('utf-8'),
                            mime_type=part.mimeType,
                        )
                    )
                else:
                    raise ValueError('Unsupported message type')
        return types.Content(parts=parts, role=message.role)

    def adk_content_to_message(
        self, content: types.Content, conversation_id: str
    ) -> Message:
        parts: list[Part] = []
        if not content.parts:
            return Message(
                parts=[],
                role=content.role if content.role == 'user' else 'agent',
                metadata={'conversation_id': conversation_id},
            )
        for part in content.parts:
            if part.text:
                # try parse as data
                try:
                    data = json.loads(part.text)
                    parts.append(DataPart(data=data))
                except:
                    parts.append(TextPart(text=part.text))
            elif part.inline_data:
                parts.append(
                    FilePart(
                        data=part.inline_data.decode('utf-8'),
                        mimeType=part.inline_data.mime_type,
                    )
                )
            elif part.file_data:
                parts.append(
                    FilePart(
                        file=FileContent(
                            uri=part.file_data.file_uri,
                            mimeType=part.file_data.mime_type,
                        )
                    )
                )
            # These aren't managed by the A2A message structure, these are internal
            # details of ADK, we will simply flatten these to json representations.
            elif part.video_metadata:
                parts.append(DataPart(data=part.video_metadata.model_dump()))
            elif part.thought:
                parts.append(TextPart(text='thought'))
            elif part.executable_code:
                parts.append(DataPart(data=part.executable_code.model_dump()))
            elif part.function_call:
                parts.append(DataPart(data=part.function_call.model_dump()))
            elif part.function_response:
                parts.extend(
                    self._handle_function_response(part, conversation_id)
                )
            else:
                raise ValueError('Unexpected content, unknown type')
        return Message(
            role=content.role if content.role == 'user' else 'agent',
            parts=parts,
            metadata={'conversation_id': conversation_id},
        )

    def _handle_function_response(
        self, part: types.Part, conversation_id: str
    ) -> list[Part]:
        parts = []
        try:
            for p in part.function_response.response['result']:
                if isinstance(p, str):
                    parts.append(TextPart(text=p))
                elif isinstance(p, dict):
                    if 'type' in p and p['type'] == 'file':
                        parts.append(FilePart(**p))
                    else:
                        parts.append(DataPart(data=p))
                elif isinstance(p, DataPart):
                    if 'artifact-file-id' in p.data:
                        file_part = self._artifact_service.load_artifact(
                            user_id=self.user_id,
                            session_id=conversation_id,
                            app_name=self.app_name,
                            filename=p.data['artifact-file-id'],
                        )
                        file_data = file_part.inline_data
                        base64_data = base64.b64encode(file_data.data).decode(
                            'utf-8'
                        )
                        parts.append(
                            FilePart(
                                file=FileContent(
                                    bytes=base64_data,
                                    mimeType=file_data.mime_type,
                                    name='artifact_file',
                                )
                            )
                        )
                    else:
                        parts.append(DataPart(data=p.data))
                else:
                    parts.append(TextPart(text=json.dumps(p)))
        except Exception as e:
            print("Couldn't convert to messages:", e)
            parts.append(DataPart(data=part.function_response.model_dump()))
        return parts


def get_message_id(m: Message | None) -> str | None:
    if not m or not m.metadata or 'message_id' not in m.metadata:
        return None
    return m.metadata['message_id']


def get_last_message_id(m: Message | None) -> str | None:
    if not m or not m.metadata or 'last_message_id' not in m.metadata:
        return None
    return m.metadata['last_message_id']


def get_conversation_id(
    t: (
        Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent | Message | None
    ),
) -> str | None:
    if (
        t
        and hasattr(t, 'metadata')
        and t.metadata
        and 'conversation_id' in t.metadata
    ):
        return t.metadata['conversation_id']
    return None


def task_still_open(task: Task | None) -> bool:
    if not task:
        return False
    return task.status.state in [
        TaskState.SUBMITTED,
        TaskState.WORKING,
        TaskState.INPUT_REQUIRED,
    ]
