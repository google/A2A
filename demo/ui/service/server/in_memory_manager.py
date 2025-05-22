import asyncio
import datetime
import uuid

from a2a.types import (
    AgentCard,
    Artifact,
    DataPart,
    Message,
    Part,
    Role,
    Task,
    TaskState,
    TaskStatus,
    TextPart,
)
from utils.agent_card import get_agent_card

from service.server import test_image
from service.server.application_manager import ApplicationManager
from service.types import Conversation, Event


class InMemoryFakeAgentManager(ApplicationManager):
    """An implementation of memory based management with fake agent actions

    This implements the interface of the ApplicationManager to plug into
    the AgentServer. This acts as the service contract that the Mesop app
    uses to send messages to the agent and provide information for the frontend.
    """

    _conversations: list[Conversation]
    _messages: list[Message]
    _tasks: list[Task]
    _events: list[Event]
    _pending_message_ids: list[str]
    _next_message_idx: int
    _agents: list[AgentCard]

    def __init__(self):
        self._conversations = []
        self._messages = []
        self._tasks = []
        self._events = []
        self._pending_message_ids = []
        self._next_message_idx = 0
        self._agents = []
        self._task_map = {}

    def create_conversation(self) -> Conversation:
        conversation_id = str(uuid.uuid4())
        c = Conversation(conversation_id=conversation_id, is_active=True)
        self._conversations.append(c)
        return c

    def sanitize_message(self, message: Message) -> Message:
        if message.contextId:
            conversation = self.get_conversation(message.contextId)
        if not conversation:
            return message
        # Check if the last event in the conversation was tied to a task.
        if conversation.messages:
            if conversation.messages[-1].taskId and task_still_open(
                next(
                    filter(
                        lambda x: x.id == conversation.messages[-1].taskId,
                        self._tasks,
                    ),
                    None,
                )
            ):
                message.taskId = conversation.messages[-1].taskId

        return message

    async def process_message(self, message: Message):
        self._messages.append(message)
        message_id = message.messageId
        context_id = message.contextId or ''
        task_id = message.taskId or ''
        if message_id:
            self._pending_message_ids.append(message_id)
        conversation = self.get_conversation(context_id)
        if conversation:
            conversation.messages.append(message)
        self._events.append(
            Event(
                id=str(uuid.uuid4()),
                actor='host',
                content=message,
                timestamp=datetime.datetime.utcnow().timestamp(),
            )
        )
        # Now actually process the message. If the response is async, return None
        # for the message response and the updated message information for the
        # incoming message (with ids attached).
        task = Task(
            id=task_id,
            contextId=context_id,
            status=TaskStatus(
                state=TaskState.submitted,
                message=message,
            ),
            history=[message],
        )
        if self._next_message_idx != 0:
            self.add_task(task)
        await asyncio.sleep(self._next_message_idx)
        response = self.next_message()
        if conversation:
            conversation.messages.append(response)
        self._events.append(
            Event(
                id=str(uuid.uuid4()),
                actor='host',
                content=response,
                timestamp=datetime.datetime.utcnow().timestamp(),
            )
        )
        self._pending_message_ids.remove(message_id)
        # Now clean up the task
        if task:
            task.status.state = TaskState.completed
            task.artifacts = [
                Artifact(
                    name='response',
                    parts=response.parts,
                    artifactId=str(uuid.uuid4()),
                )
            ]
            if not task.history:
                task.history = [response]
            else:
                task.history.append(response)
            self.update_task(task)

    def add_task(self, task: Task):
        self._tasks.append(task)

    def update_task(self, task: Task):
        for i, t in enumerate(self._tasks):
            if t.id == task.id:
                self._tasks[i] = task
                return

    def add_event(self, event: Event):
        self._events.append(event)

    def next_message(self) -> Message:
        message = _message_queue[self._next_message_idx]
        self._next_message_idx = (self._next_message_idx + 1) % len(
            _message_queue
        )
        return message

    def get_conversation(
        self, conversation_id: str | None
    ) -> Conversation | None:
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
        rval: list[tuple[str, str]] = []
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
        return [(x, '') for x in self._pending_message_ids]

    def register_agent(self, url):
        agent_data = get_agent_card(url)
        if not agent_data.url:
            agent_data.url = url
        self._agents.append(agent_data)

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
        return []


_contextId = str(uuid.uuid4())

# This represents the precanned responses that will be returned in order.
# Extend this list to test more functionality of the UI
_message_queue: list[Message] = [
    Message(
        role=Role.agent,
        parts=[Part(root=TextPart(text='Hello'))],
        contextId=_contextId,
        messageId=str(uuid.uuid4()),
    ),
    Message(
        role=Role.agent,
        parts=[
            Part(
                root=DataPart(
                    data={
                        'type': 'form',
                        'form': {
                            'type': 'object',
                            'properties': {
                                'name': {
                                    'type': 'string',
                                    'description': 'Enter your name',
                                    'title': 'Name',
                                },
                                'date': {
                                    'type': 'string',
                                    'format': 'date',
                                    'description': 'Birthday',
                                    'title': 'Birthday',
                                },
                            },
                            'required': ['date'],
                        },
                        'form_data': {
                            'name': 'John Smith',
                        },
                        'instructions': 'Please provide your birthday and name',
                    }
                )
            ),
        ],
        contextId=_contextId,
        messageId=str(uuid.uuid4()),
    ),
    Message(
        role=Role.agent,
        parts=[Part(root=TextPart(text='I like cats'))],
        contextId=_contextId,
        messageId=str(uuid.uuid4()),
    ),
    test_image.make_test_image(_contextId),
    Message(
        role=Role.agent,
        parts=[Part(root=TextPart(text='And I like dogs'))],
        contextId=_contextId,
        messageId=str(uuid.uuid4()),
    ),
]
