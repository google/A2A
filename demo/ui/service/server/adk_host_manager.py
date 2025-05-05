import asyncio
import datetime
import json
import os
from typing import Tuple, Optional, Any
import uuid
from service.types import Conversation, Event
from common.types import (
    Message,
    Task,
    TextPart,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    Artifact,
    AgentCard,
    DataPart,
    FilePart,
    FileContent,
    Part,
)
from hosts.multiagent.host_agent import HostAgent # Assuming this path is correct
from hosts.multiagent.remote_agent_connection import ( # Assuming this path is correct
    TaskCallbackArg,
)
from utils.agent_card import get_agent_card # Assuming this path is correct
from service.server.application_manager import ApplicationManager
from google.adk import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService
# Ensure GenAIEvent is imported or use the correct type hint
from google.adk.events.event import Event as ADKEvent
from google.adk.events.event_actions import EventActions as ADKEventActions
from google.genai import types
import base64
import traceback # Import traceback for error printing

class ADKHostManager(ApplicationManager):
    """An implementation of memory based management with agent actions.

    This implements the interface of the ApplicationManager to plug into
    the AgentServer. This acts as the service contract that the Mesop app
    uses to send messages to the agent and provide information for the frontend.
    """
    _conversations: list[Conversation]
    _messages: list[Message] # Note: Use conversation.messages as primary store
    _tasks: list[Task]
    _events: dict[str, Event]
    _pending_message_ids: list[str] # Tracks user messages awaiting agent response
    _agents: list[AgentCard]
    _task_map: dict[str, str] # Maps message_id to task_id

    def __init__(self, api_key: str = "", uses_vertex_ai: bool = False):
        self._conversations = []
        self._messages = [] # Consider if this global list is truly needed
        self._tasks = []
        self._events = {} # Stores Events for UI history/debugging
        self._pending_message_ids = []
        self._agents = []
        self._artifact_chunks = {}
        self._session_service = InMemorySessionService()
        self._artifact_service = InMemoryArtifactService()
        self._memory_service = InMemoryMemoryService()
        # Pass the callback to the HostAgent
        self._host_agent = HostAgent([], self.task_callback)
        self.user_id = "test_user"
        self.app_name = "A2A"
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY", "")
        self.uses_vertex_ai = uses_vertex_ai or os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").upper() == "TRUE"
        self._ready_event = asyncio.Event()

        # Set environment variables based on auth method
        if self.uses_vertex_ai:
            os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
            # Ensure API key env var is unset if using Vertex AI ADC
            if "GOOGLE_API_KEY" in os.environ:
                 del os.environ["GOOGLE_API_KEY"]
        elif self.api_key:
            # Use API key authentication
            os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
            os.environ["GOOGLE_API_KEY"] = self.api_key
        else:
             # Handle case where neither is set - ADK might raise error later
             print("[WARN] Neither Vertex AI nor GOOGLE_API_KEY seems to be configured.")

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            asyncio.create_task(self._initialize_host())
        else:
            # No running loop yet: defer it manually
            asyncio.get_event_loop().call_soon_threadsafe(
                lambda: asyncio.create_task(self._initialize_host())
            )
        # Map of message id to task id
        self._task_map = {}
        # Map to manage 'lost' message ids (less critical now with better state mgmt)
        # self._next_id = {} # dict[str, str]: previous message to next message

    def update_api_key(self, api_key: str):
        """Update the API key and reinitialize the host if needed"""
        if api_key and api_key != self.api_key:
            print("[INFO] Updating API key and reinitializing ADK Host.")
            self.api_key = api_key

            # Only update if not using Vertex AI
            if not self.uses_vertex_ai:
                os.environ["GOOGLE_API_KEY"] = api_key
                # Reinitialize host with new API key
                asyncio.create_task(self._initialize_host())
            else:
                 print("[WARN] Attempted to update API key while using Vertex AI auth. Ignoring.")


    async def _initialize_host(self):
        """Initializes or re-initializes the ADK Runner and HostAgent."""
        print("[INFO] Initializing ADK HostAgent and Runner...")

        # 🔥 NEW: dynamically load existing remote agents
        from service.client.client import ConversationClient
        from service.types import ListAgentRequest

        client = ConversationClient("http://localhost:12000")  # Local server

        try:
            response = await client.list_agents(ListAgentRequest())
            remote_agents = response.result
            self._agents = remote_agents
            print(f"[INFO] Loaded {len(self._agents)} remote agents.")
        except Exception as e:
            print(f"[WARN] Failed to load remote agents during _initialize_host: {e}")

        # Build HostAgent with up-to-date agent list
        self._host_agent = HostAgent(self._agents, self.task_callback)

        agent_logic = self._host_agent.create_agent()

        self._host_runner = Runner(
            app_name=self.app_name,
            agent=agent_logic,
            artifact_service=self._artifact_service,
            session_service=self._session_service,
            memory_service=self._memory_service,
        )
        self._ready_event.set()
        print("[INFO] ADK HostAgent and Runner initialized.")

    def create_conversation(self) -> Conversation:
        """Creates a new conversation session."""
        print("[INFO] Creating new conversation...")
        session = self._session_service.create_session(
            app_name=self.app_name,
            user_id=self.user_id)
        conversation_id = session.id

        session.state = {}
        print(f"[DEBUG] Initialized state for newly created ADK session {conversation_id} in create_conversation.")

        # Create the conversation state object
        c = Conversation(
            conversation_id=conversation_id,
            is_active=True,
            name=f"Conversation {len(self._conversations) + 1}", # Assign default name
            messages=[] # Initialize with empty message list
        )
        self._conversations.append(c)
        print(f"[INFO] Conversation created with ID: {conversation_id}")
        return c

    def sanitize_message(self, message: Message) -> Message:
        """Ensures message has necessary metadata (message_id, last_message_id)."""
        if not message.metadata:
            message.metadata = {}

        # Assign message_id if not present
        if 'message_id' not in message.metadata or not message.metadata['message_id']:
            message.metadata['message_id'] = str(uuid.uuid4())
            # print(f"[DEBUG] Sanitized message: Assigned message_id={message.metadata['message_id']}")

        if 'conversation_id' in message.metadata:
            conversation = self.get_conversation(message.metadata['conversation_id'])
            if conversation:
                # Add last_message_id if messages exist *in the backend conversation state*
                if conversation.messages:
                    # Find the *actual* last message saved in the backend conversation state
                    last_saved_message = conversation.messages[-1]
                    last_message_id = get_message_id(last_saved_message)
                    if last_message_id:
                        # Add it to the incoming message's metadata *before* it's saved
                        # Only add if not already present or different?
                        if 'last_message_id' not in message.metadata:
                             message.metadata['last_message_id'] = last_message_id
                             # print(f"[DEBUG] Sanitized message: Added last_message_id={last_message_id}")
            # else:
            #      print(f"[WARN] sanitize_message: Conversation {message.metadata['conversation_id']} not found while adding last_message_id.")
        # else:
        #      print("[WARN] sanitize_message: conversation_id missing in metadata.")

        return message

    # ************************************************************************
    # *process_message* is the core logic handling incoming user messages *
    # ************************************************************************
    async def process_message(self, message: Message):
        """Processes a user message, runs the agent, and saves the response."""
        conversation_id = message.metadata.get('conversation_id')
        message_id = get_message_id(message)

        if not message_id or not conversation_id:
            print(f"[ERROR] process_message: Missing metadata. message_id={message_id}, conversation_id={conversation_id}. Aborting.")
            return

        if not self._ready_event.is_set():
            print("[INFO] Waiting for HostAgent to initialize...")
            await self._ready_event.wait()
        print("[INFO] HostAgent is ready. Processing message...")

        print(f"[INFO] process_message started for message_id: {message_id} in conversation: {conversation_id}")

        if message_id not in self._pending_message_ids:
            self._pending_message_ids.append(message_id)
            print(f"[DEBUG] Added message_id {message_id} to pending.")

        conversation = self.get_conversation(conversation_id)
        if not conversation:
            print(f"[ERROR] process_message: Conversation {conversation_id} not found!")
            if message_id in self._pending_message_ids:
                self._pending_message_ids.remove(message_id)
            return

        if not any(get_message_id(m) == message_id for m in conversation.messages):
            conversation.messages.append(message)
            print(f"[DEBUG] Appended user message {message_id} to conversation {conversation_id}.")

        self.add_event(Event(
            id=str(uuid.uuid4()),
            actor='user',
            content=message,
            timestamp=datetime.datetime.utcnow().timestamp(),
        ))

        # State to inject into the session
        state_update = {
            'input_message_metadata': message.metadata,
            'session_id': conversation_id,
        }

        target_agent_url = message.metadata.get('remote_agent_url')
        if target_agent_url:
            state_update['target_agent_url'] = target_agent_url
            print(f"[INFO] Injecting target_agent_url into state_delta: {target_agent_url}")

        last_message_id_in_meta = get_last_message_id(message)
        if last_message_id_in_meta and last_message_id_in_meta in self._task_map:
            task_id_to_resume = self._task_map[last_message_id_in_meta]
            task_obj = next((t for t in self._tasks if t.id == task_id_to_resume), None)
            if task_still_open(task_obj):
                state_update['task_id'] = task_id_to_resume
                print(f"[INFO] Resuming task_id: {task_id_to_resume}")

        # 🧠 Session Management
        try:
            session = self._session_service.get_session(
                app_name=self.app_name,
                user_id=self.user_id,
                session_id=conversation_id,
            )
            if session is None:
                print(f"[WARN] No session found, creating new session {conversation_id}.")
                session = self._session_service.create_session(
                    app_name=self.app_name,
                    user_id=self.user_id,
                    session_id=conversation_id,
                )
                session.state = {}

            if session.state is None:
                print(f"[WARN] Session {conversation_id} exists but state was None, initializing.")
                session.state = {}

            print(f"[DEBUG LOCK] State before Call 1: {session.state}, Type: {type(session.state)}, ID: {id(session.state)}")

            # -- Call 1: Append initial state_update
            self._session_service.append_event(session, ADKEvent(
                id=ADKEvent.new_id(),
                author="host_agent",
                invocation_id=ADKEvent.new_id(),
                actions=ADKEventActions(state_delta=state_update),
            ))
            print(f"[DEBUG LOCK] State after Call 1: {session.state}, ID: {id(session.state)}")

            # -- Call 2: Inject system prompt
            if message.role == "user":
                if session.state is None:
                    print(f"[WARN LOCK] State became None before Call 2. Reinitializing.")
                    session.state = {}

                system_instructions = (
                    "You MUST follow these rules strictly:\n\n"
                    "- You are a host agent that routes messages to remote agents.\n"
                    "- The user has added one or more remote agents to this system.\n"
                    "- You MUST NOT ask the user to pick an agent if `target_agent_url` exists.\n"
                    "- If `target_agent_url` exists in session state, IMMEDIATELY call the `send_task` tool using the user's input.\n"
                    "- DO NOT ask the user to pick an agent if `target_agent_url` exists.\n"
    "- DO NOT prompt or clarify. If `target_agent_url` is present, just call `send_task`.\n"
                    "- If no `target_agent_url` is present, THEN you may ask the user to select an agent.\n"
                    "- If the user asks for a list of available agents, call `list_remote_agents`.\n"
                    "- Otherwise, respond as you normally would."
                )
                print(f"[DEBUG LOCK] State before Call 2: {session.state}, ID: {id(session.state)}")

                self._session_service.append_event(session, ADKEvent(
                    id=ADKEvent.new_id(),
                    author="host_agent",
                    invocation_id=ADKEvent.new_id(),
                    actions=ADKEventActions(state_delta={
                        "messages": [
                            {"role": "system", "parts": [{"text": system_instructions}]}
                        ]
                    }),
                ))

                print(f"[DEBUG LOCK] State after Call 2: {session.state}, ID: {id(session.state)}")

        except Exception as e:
            print(f"[ERROR LOCK] Exception during session event appending: {e}")
            traceback.print_exc()
            if message_id in self._pending_message_ids:
                self._pending_message_ids.remove(message_id)
            return

        # 🧠 Run HostAgent with Session
        final_agent_event: Optional[GenAIEvent] = None
        agent_response: Optional[Message] = None
        try:
            print(f"[INFO] Calling _host_runner.run_async for session {conversation_id}, message {message_id}")

            async for event in self._host_runner.run_async(
                user_id=self.user_id,
                session_id=conversation_id,
                new_message=self.adk_content_from_message(message)
            ):
                self.add_event(Event(
                    id=event.id,
                    actor=event.author,
                    content=self.adk_content_to_message(event.content, conversation_id),
                    timestamp=event.timestamp,
                ))

                if conversation and event.content.role != 'user':
                    conversation.messages.append(self.adk_content_to_message(event.content, conversation_id))

                final_agent_event = event

            print(f"[INFO] _host_runner.run_async finished for message {message_id}")

            if final_agent_event and final_agent_event.author not in ['user', 'host_agent']:
                print(f"[DEBUG] Processing final event {final_agent_event.id} as agent response.")

                if final_agent_event.content.role != 'agent':
                    final_agent_event.content.role = 'agent'

                agent_response = self.adk_content_to_message(final_agent_event.content, conversation_id)

                if agent_response:
                    if not agent_response.metadata:
                        agent_response.metadata = {}
                    agent_response.metadata.update({
                        'conversation_id': conversation_id,
                        'message_id': str(uuid.uuid4()),
                        'last_message_id': message_id,
                        'remote_agent_url': target_agent_url or message.metadata.get('remote_agent_url')
                    })

                    if conversation and not any(get_message_id(m) == agent_response.metadata['message_id'] for m in conversation.messages):
                        conversation.messages.append(agent_response)
                        print(f"[INFO] Appended agent response {agent_response.metadata['message_id']} to conversation {conversation_id}")

        except Exception as e:
            print(f"[ERROR] Exception during HostAgent run: {e}")
            traceback.print_exc()
            if conversation:
                error_message = Message(
                    role="agent",
                    parts=[TextPart(text="Sorry, an error occurred while processing your request.")],
                    metadata={
                        'conversation_id': conversation_id,
                        'message_id': str(uuid.uuid4()),
                        'last_message_id': message_id,
                        'is_error': True,
                    }
                )
                conversation.messages.append(error_message)
                print(f"[INFO] Appended error message to conversation {conversation_id}")

        finally:
            if message_id in self._pending_message_ids:
                self._pending_message_ids.remove(message_id)
                print(f"[DEBUG] Removed message_id {message_id} from pending list.")
            print(f"[INFO] process_message finished for message_id: {message_id}")

    # --- Task Management Methods ---

    def add_task(self, task: Task):
        """Adds a new task to the internal list."""
        # Avoid duplicates
        if not any(t.id == task.id for t in self._tasks):
             self._tasks.append(task)
             print(f"[DEBUG] Added task {task.id}")
        # else:
        #      print(f"[WARN] Attempted to add duplicate task {task.id}")


    def update_task(self, task: Task):
        """Updates an existing task in the internal list."""
        for i, t in enumerate(self._tasks):
            if t.id == task.id:
                self._tasks[i] = task
                # print(f"[DEBUG] Updated task {task.id}")
                return
        # If task not found, maybe add it? Or log warning.
        # print(f"[WARN] update_task: Task {task.id} not found to update. Adding instead.")
        # self.add_task(task)


    # ************************************************************************
    # *task_callback* handles updates received from the HostAgent *
    # * regarding remote agent progress (status, artifacts) *
    # ************************************************************************
    def task_callback(self, task_update: TaskCallbackArg, agent_card: AgentCard):
        """Callback function invoked by HostAgent with task updates."""
        task_id = getattr(task_update, 'id', 'N/A')
        print(f"[INFO] task_callback received update: type={type(task_update).__name__}, task_id={task_id}, agent={agent_card.name}")

        # Emit event for UI history/debug
        self.emit_event(task_update, agent_card)

        conversation_id = get_conversation_id(task_update)
        conversation = self.get_conversation(conversation_id) if conversation_id else None

        current_task_state: Optional[Task] = None # Define outside if/elif

        # --- Handle Task Status Updates ---
        if isinstance(task_update, TaskStatusUpdateEvent):
            current_task_state = self.add_or_get_task(task_update) # Get or create task object
            current_task_state.status = task_update.status # Update status
            # Associate originating message with this task if possible
            self.attach_message_to_task(task_update.status.message, current_task_state.id)
            # Add message to task history if needed by agent logic
            self.insert_message_history(current_task_state, task_update.status.message)
            # Update the task list
            self.update_task(current_task_state)
            # Trace message flow if IDs are present
            self.insert_id_trace(task_update.status.message)

            # ** Check if this status update contains the final message **
            # This depends on the remote agent's protocol. Assume COMPLETED state signifies the end.
            if task_update.status.state == TaskState.COMPLETED and task_update.status.message:
                print(f"[INFO] task_callback detected COMPLETED status with message for task {current_task_state.id}")
                final_message = task_update.status.message
                # Ensure necessary metadata is present
                response_message_id = get_message_id(final_message) or str(uuid.uuid4())
                final_message.metadata = final_message.metadata or {}
                final_message.metadata['conversation_id'] = conversation_id
                final_message.metadata['message_id'] = response_message_id
                # Ensure role is set correctly
                if final_message.role != 'agent': final_message.role = 'agent'

                # Append the final message to the main conversation state
                if conversation:
                    if not any(get_message_id(m) == response_message_id for m in conversation.messages):
                        conversation.messages.append(final_message)
                        print(f"[INFO] Appended final message {response_message_id} from task_callback/COMPLETED status to conversation {conversation_id}.")
                        # Potentially remove originating user message from pending?
                        # Need link from task_id back to original user message_id
                        # If task_id was mapped from user message_id earlier...
                        originating_user_msg_id = next((msg_id for msg_id, t_id in self._task_map.items() if t_id == current_task_state.id), None)
                        if originating_user_msg_id and originating_user_msg_id in self._pending_message_ids:
                             self._pending_message_ids.remove(originating_user_msg_id)
                             print(f"[DEBUG] Removed originating user message {originating_user_msg_id} from pending via task_callback completion.")

                    # else:
                    #      print(f"[WARN] Final message {response_message_id} from task_callback already exists in conversation {conversation_id}.")
                else:
                    print(f"[ERROR] task_callback: No conversation object found for completed task message: {conversation_id}")

            return current_task_state # Return updated task state

        # --- Handle Task Artifact Updates ---
        elif isinstance(task_update, TaskArtifactUpdateEvent):
            current_task_state = self.add_or_get_task(task_update)
            self.process_artifact_event(current_task_state, task_update) # Assemble chunks
            self.update_task(current_task_state) # Save updated task with new artifact
            # Artifacts are usually attached to tasks, not directly to conversation messages
            return current_task_state

        # --- Handle Full Task Object Updates (Less common for remote agents?) ---
        elif isinstance(task_update, Task):
            current_task_state = task_update # The update *is* the task object
            existing_task = next(filter(lambda x: x.id == current_task_state.id, self._tasks), None)
            # Link message<->task and trace IDs
            self.attach_message_to_task(current_task_state.status.message, current_task_state.id)
            self.insert_id_trace(current_task_state.status.message)

            if not existing_task:
                self.add_task(current_task_state)
                print(f"[INFO] Added new task {current_task_state.id} via full Task object in task_callback.")
            else:
                self.update_task(current_task_state)
                # print(f"[DEBUG] Updated task {current_task_state.id} via full Task object in task_callback.")

            # ** Check if this Task object represents the final state **
            if current_task_state.status.state == TaskState.COMPLETED and current_task_state.status.message:
                print(f"[INFO] task_callback detected COMPLETED Task object with message for task {current_task_state.id}")
                final_message = current_task_state.status.message
                response_message_id = get_message_id(final_message) or str(uuid.uuid4())
                final_message.metadata = final_message.metadata or {}
                final_message.metadata['conversation_id'] = conversation_id
                final_message.metadata['message_id'] = response_message_id
                if final_message.role != 'agent': final_message.role = 'agent'

                # Append to conversation state
                if conversation:
                    if not any(get_message_id(m) == response_message_id for m in conversation.messages):
                        conversation.messages.append(final_message)
                        print(f"[INFO] Appended final message {response_message_id} from task_callback/COMPLETED Task object to conversation {conversation_id}.")
                        # Remove pending user message if possible
                        originating_user_msg_id = next((msg_id for msg_id, t_id in self._task_map.items() if t_id == current_task_state.id), None)
                        if originating_user_msg_id and originating_user_msg_id in self._pending_message_ids:
                             self._pending_message_ids.remove(originating_user_msg_id)
                             print(f"[DEBUG] Removed originating user message {originating_user_msg_id} from pending via task_callback/Task completion.")
                    # else:
                    #      print(f"[WARN] Final message {response_message_id} from task_callback/Task object already exists in conversation {conversation_id}.")
                else:
                    print(f"[ERROR] task_callback: No conversation object found for completed Task object message: {conversation_id}")

            return current_task_state # Return the updated/added task state
        else:
            print(f"[WARN] Unhandled type received in task_callback: {type(task_update)}")
            return None # Indicate no task state returned/updated


    def emit_event(self, task_data: TaskCallbackArg, agent_card: AgentCard):
        """Creates and stores an Event based on task callback data."""
        content: Optional[Message] = None
        conversation_id = get_conversation_id(task_data)
        base_metadata = {'conversation_id': conversation_id} if conversation_id else {}

        if isinstance(task_data, TaskStatusUpdateEvent):
            if task_data.status.message:
                content = task_data.status.message
                # Ensure metadata has conversation_id
                if content.metadata: content.metadata.update(base_metadata)
                else: content.metadata = base_metadata
            else: # Create a simple text event for status change
                content = Message(
                    parts=[TextPart(text=f"Task status changed: {task_data.status.state}")],
                    role="system", # Status updates are like system events
                    metadata=base_metadata,
                )
        elif isinstance(task_data, TaskArtifactUpdateEvent):
            content = Message(
                parts=task_data.artifact.parts,
                role="agent", # Artifacts come from the agent
                metadata=base_metadata, # Attach conversation ID
            )
        elif isinstance(task_data, Task): # Handle full Task object
             if task_data.status and task_data.status.message:
                  content = task_data.status.message
                  if content.metadata: content.metadata.update(base_metadata)
                  else: content.metadata = base_metadata
             elif task_data.artifacts: # If no message, maybe event for artifacts?
                  parts = []
                  for a in task_data.artifacts: parts.extend(a.parts)
                  content = Message(parts=parts, role="agent", metadata=base_metadata)
             else: # Fallback to status state
                  content = Message(
                       parts=[TextPart(text=f"Task update: {task_data.status.state}")],
                       role="system", metadata=base_metadata
                  )
        else: # Fallback for unknown types
             content = Message(parts=[TextPart(text="Task update received")], role="system", metadata=base_metadata)

        # Ensure content is a Message object before creating event
        if isinstance(content, Message):
             event_id = str(uuid.uuid4())
             self.add_event(Event(
                 id=event_id,
                 actor=agent_card.name, # Attribute event to the specific agent
                 content=content,
                 timestamp=datetime.datetime.utcnow().timestamp(),
             ))
        # else:
        #      print(f"[WARN] emit_event: Could not determine Message content for task_data type {type(task_data)}")


    def attach_message_to_task(self, message: Message | None, task_id: str):
        """Links a message ID to a task ID if the message has an ID."""
        message_id = get_message_id(message)
        if message_id and task_id:
             if message_id not in self._task_map:
                 self._task_map[message_id] = task_id
                 # print(f"[DEBUG] Mapped message_id {message_id} to task_id {task_id}")
             # else: # Handle case where message might be linked to multiple tasks? Or update?
                 # print(f"[WARN] Message {message_id} already mapped to task {self._task_map[message_id]}. Not remapping to {task_id}.")


    def insert_id_trace(self, message: Message | None):
        """Records the relationship between consecutive messages (if IDs exist)."""
        # This seems less critical now but harmless to keep if needed elsewhere
        # message_id = get_message_id(message)
        # last_message_id = get_last_message_id(message)
        # if message_id and last_message_id:
        #     self._next_id[last_message_id] = message_id
        pass # Currently disabling this as it seems unused


    def insert_message_history(self, task: Task, message: Message | None):
        """Adds a message to a task's specific history list."""
        if not message: return
        if task.history is None: task.history = [] # Initialize if needed

        message_id = get_message_id(message)
        if not message_id:
             # print("[WARN] insert_message_history: Message lacks ID, cannot add to history.")
             return

        # Add message to task history only if not already present
        if not any(get_message_id(hist_msg) == message_id for hist_msg in task.history):
            task.history.append(message)
            # print(f"[DEBUG] Added message {message_id} to history of task {task.id}")
        # else:
        #     print(f"[DEBUG] Message {message_id} already in history of task {task.id}")


    def add_or_get_task(self, task_update_data: TaskCallbackArg) -> Task:
        """Finds an existing Task by ID or creates a new one."""
        task_id = getattr(task_update_data, 'id', None)
        if not task_id:
             # This shouldn't happen if task updates always have an ID
             print("[ERROR] add_or_get_task: Task update data lacks an ID!")
             # Create a dummy task? Requires careful thought. Returning placeholder.
             return Task(id="UNKNOWN_TASK", status=TaskStatus(state=TaskState.ERROR))

        current_task = next(filter(lambda x: x.id == task_id, self._tasks), None)
        if not current_task:
            print(f"[INFO] add_or_get_task: Task {task_id} not found. Creating new Task state.")
            conversation_id = get_conversation_id(task_update_data)
            current_task = Task(
                id=task_id,
                # Initialize status based on update type if possible, else default
                status=getattr(task_update_data, 'status', TaskStatus(state=TaskState.SUBMITTED)),
                metadata=getattr(task_update_data, 'metadata', {'conversation_id': conversation_id}),
                artifacts=[], # Start with empty artifacts
                history=[], # Start with empty history
                sessionId=conversation_id,
            )
            self.add_task(current_task) # Add the newly created task to the main list

        return current_task


    def process_artifact_event(self, current_task: Task, task_update_event: TaskArtifactUpdateEvent):
        """Handles artifact chunks and appends complete artifacts to the task."""
        # This logic seems okay, handles chunking based on append/lastChunk flags
        artifact = task_update_event.artifact
        task_id = task_update_event.id # ID of the task this artifact belongs to
        artifact_index = artifact.index # Index of the artifact within the task (for chunking)

        # Ensure task has an artifact list initialized
        if current_task.artifacts is None: current_task.artifacts = []

        if not artifact.append: # First chunk (or only chunk)
            if artifact.lastChunk is None or artifact.lastChunk:
                # Single, complete artifact payload
                print(f"[DEBUG] process_artifact_event: Received complete artifact (Index {artifact_index}) for task {task_id}.")
                # Add directly to the task's artifact list (check index collision?)
                # Simple append for now, might need index management later
                current_task.artifacts.append(artifact)
            else:
                # First chunk of a multi-chunk artifact
                print(f"[DEBUG] process_artifact_event: Received first chunk for artifact (Index {artifact_index}) for task {task_id}.")
                # Store chunk temporarily, keyed by task_id and artifact_index
                if task_id not in self._artifact_chunks: self._artifact_chunks[task_id] = {}
                self._artifact_chunks[task_id][artifact_index] = artifact
        else: # Appending chunk
            print(f"[DEBUG] process_artifact_event: Received append chunk for artifact (Index {artifact_index}) for task {task_id}.")
            if task_id in self._artifact_chunks and artifact_index in self._artifact_chunks[task_id]:
                # Find the stashed artifact to append to
                current_temp_artifact = self._artifact_chunks[task_id][artifact_index]
                current_temp_artifact.parts.extend(artifact.parts) # Append parts

                if artifact.lastChunk:
                    # This was the final chunk, move completed artifact to task
                    print(f"[DEBUG] process_artifact_event: Received last chunk. Finalizing artifact (Index {artifact_index}) for task {task_id}.")
                    current_task.artifacts.append(current_temp_artifact)
                    # Clean up temporary storage
                    del self._artifact_chunks[task_id][artifact_index]
                    if not self._artifact_chunks[task_id]: # Remove task entry if no more chunks pending
                         del self._artifact_chunks[task_id]
            else:
                 print(f"[WARN] process_artifact_event: Received append chunk for unknown/unstored artifact (Task {task_id}, Index {artifact_index}). Ignoring.")


    def add_event(self, event: Event):
        """Adds an event to the internal event dictionary."""
        if event and event.id:
             self._events[event.id] = event
        # else:
        #      print("[WARN] add_event: Attempted to add an event without an ID.")


    def get_conversation(self, conversation_id: Optional[str]) -> Optional[Conversation]:
        """Retrieves a conversation object by its ID."""
        if not conversation_id: return None
        return next(
            filter(lambda c: c.conversation_id == conversation_id, self._conversations),
            None
        )

    def get_pending_messages(self) -> list[Tuple[str, str]]:
        """Gets messages currently awaiting processing, potentially with status hints."""
        rval = []
        # Iterate safely over a copy in case the list is modified during iteration elsewhere
        for message_id in list(self._pending_message_ids):
            status_hint = "Processing..." # Default hint
            if message_id in self._task_map:
                task_id = self._task_map[message_id]
                task = next(filter(lambda x: x.id == task_id, self._tasks), None)
                if task and task.history:
                     # Try to get a more specific hint from the last message in task history
                     last_hist_msg = task.history[-1]
                     if last_hist_msg.parts:
                          part = last_hist_msg.parts[0]
                          if part.type == "text":
                               status_hint = part.text[:100] + ("..." if len(part.text)>100 else "") # Truncate long hints
                          else:
                               status_hint = f"Working ({part.type})..."
                     elif task.status.state != TaskState.WORKING:
                          # If no parts, use the task state if it's not 'WORKING'
                          status_hint = f"Task state: {task.status.state}"

            rval.append((message_id, status_hint))
        return rval


    def register_agent(self, url):
        """Registers a new remote agent by fetching its card."""
        print(f"[INFO] Registering agent from URL: {url}")
        try:
            agent_data = get_agent_card(url) # Fetch agent details
            if not agent_data:
                 print(f"[ERROR] Failed to get agent card from {url}")
                 return

            if not agent_data.url: agent_data.url = url # Ensure URL is stored

            # Avoid adding duplicate agents
            if not any(a.url == agent_data.url for a in self._agents):
                self._agents.append(agent_data)
                print(f"[INFO] Registered agent: {agent_data.name} ({agent_data.url})")
                # Re-initialize the host runner with the updated agent list
                # This is crucial for the HostAgent to be aware of the new agent
                asyncio.create_task(self._initialize_host())
            # else:
            #     print(f"[WARN] Agent with URL {agent_data.url} already registered.")

        except Exception as e:
            print(f"[ERROR] Failed to register agent from {url}: {e}")
            traceback.print_exc()

    # --- Properties to expose state ---

    @property
    def agents(self) -> list[AgentCard]:
        return self._agents

    @property
    def conversations(self) -> list[Conversation]:
        # Return a copy to prevent external modification? Or trust consumers?
        return self._conversations

    @property
    def tasks(self) -> list[Task]:
        return self._tasks

    @property
    def events(self) -> list[Event]:
        # Return events sorted by timestamp for UI display
        return sorted(self._events.values(), key=lambda x: x.timestamp)


    # --- ADK Content Conversion Utilities ---

    def adk_content_from_message(self, message: Message) -> types.Content:
        """Converts internal Message format to google.genai.types.Content."""
        parts: list[types.Part] = []
        for part in message.parts:
            if part.type == "text":
                parts.append(types.Part.from_text(text=part.text))
            elif part.type == "data":
                try:
                     json_string = json.dumps(part.data)
                     parts.append(types.Part.from_text(text=json_string))
                except Exception as e:
                     print(f"[WARN] Failed to dump data part to JSON: {e}. Sending as text.")
                     parts.append(types.Part.from_text(text=str(part.data)))
            elif part.type == "file":
                 # Assuming FilePart has file attribute of type FileContent
                 if hasattr(part, 'file') and part.file:
                      if part.file.uri:
                           parts.append(types.Part.from_uri(
                               file_uri=part.file.uri,
                               mime_type=part.file.mimeType
                           ))
                      elif part.file.bytes: # Expects base64 encoded string? ADK expects bytes.
                           try:
                                file_bytes = base64.b64decode(part.file.bytes)
                                parts.append(types.Part.from_data( # Use from_data for bytes
                                     data=file_bytes,
                                     mime_type=part.file.mimeType)
                                )
                           except Exception as e:
                                print(f"[ERROR] Failed to decode base64 bytes for file part: {e}")
                      # else: print("[WARN] File part has no URI or bytes.")
                 # else: print("[WARN] File part missing 'file' attribute or FileContent.")
            # else: print(f"[WARN] Unsupported part type for ADK conversion: {part.type}")
        return types.Content(parts=parts, role=message.role)


    def adk_content_to_message(self, content: types.Content, conversation_id: str) -> Message:
        """Converts google.genai.types.Content back to internal Message format."""
        parts: list[Part] = []
        if not content.parts: # Handle empty content
            return Message(
                parts=[],
                role=content.role if content.role == 'user' else 'agent',
                metadata={'conversation_id': conversation_id},
            )

        for part in content.parts:
            # Prioritize specific types over just text if possible
            if part.function_call:
                parts.append(DataPart(data=part.function_call.model_dump()))
            elif part.function_response:
                # Flatten function response results into message parts
                parts.extend(self._handle_function_response(part, conversation_id))
            elif part.inline_data: # Raw data (bytes)
                 # Encode bytes as base64 string for JSON compatibility in our Message
                 base64_data = base64.b64encode(part.inline_data.data).decode('utf-8')
                 parts.append(FilePart(
                      file=FileContent(
                           bytes=base64_data,
                           mimeType=part.inline_data.mime_type,
                           # name=? # Consider adding name if available
                      )
                 ))
            elif part.file_data: # URI reference
                parts.append(FilePart(
                    file=FileContent(
                        uri=part.file_data.file_uri,
                        mimeType=part.file_data.mime_type
                    )
                ))
            elif part.text: # Process text last as fallback
                # Try parsing as JSON data first, might be structured content
                try:
                    data = json.loads(part.text)
                    # Basic check if it looks like our other part types (e.g., FilePart)
                    if isinstance(data, dict) and 'type' in data and data['type'] in ['file', 'data']:
                         # Attempt to reconstruct the original Part type if possible
                         if data['type'] == 'file': parts.append(FilePart(**data))
                         else: parts.append(DataPart(**data))
                    else:
                         # Assume it's just arbitrary JSON data
                         parts.append(DataPart(data=data))
                except json.JSONDecodeError:
                    # If not JSON, treat as plain text
                    parts.append(TextPart(text=part.text))
                except Exception as e:
                     print(f"[WARN] Error processing potential JSON in text part: {e}. Treating as plain text.")
                     parts.append(TextPart(text=part.text))

            # Handle other ADK-specific types if needed (flattening them)
            elif part.executable_code:
                 parts.append(DataPart(data=part.executable_code.model_dump()))
            elif part.video_metadata:
                 parts.append(DataPart(data=part.video_metadata.model_dump()))
            # elif part.thought: parts.append(TextPart(text=f"Thought: {part.thought}")) # Represent thought?
            else:
                 print(f"[WARN] Unexpected/unhandled ADK part type: {part}")
                 # Fallback: represent as plain text
                 parts.append(TextPart(text=f"<{type(part).__name__}>"))


        return Message(
            # Use ADK role, default to 'agent' if it's not 'user'
            role=content.role if content.role == 'user' else 'agent',
            parts=parts,
            metadata={'conversation_id': conversation_id}, # Ensure conversation ID is attached
        )


    def _handle_function_response(self, part: types.Part, conversation_id: str) -> list[Part]:
        """Flattens the results within a function response Part into message Parts."""
        # This function assumes response['result'] is iterable and contains primitive types or dicts
        parts = []
        try:
            # Check if response and result exist
            if not part.function_response.response or 'result' not in part.function_response.response:
                 print("[WARN] Function response part lacks 'result' field.")
                 # Represent the raw response data
                 parts.append(DataPart(data=part.function_response.model_dump()))
                 return parts

            result_data = part.function_response.response['result']
            # Handle if result is not iterable (e.g., a single string/dict)
            if not isinstance(result_data, (list, tuple)):
                 result_data = [result_data] # Wrap non-iterable in a list

            for item in result_data:
                if isinstance(item, str):
                    parts.append(TextPart(text=item))
                elif isinstance(item, dict):
                    # Check if it matches our known Part structures
                    if 'type' in item and item['type'] == 'file' and 'file' in item:
                         parts.append(FilePart(**item))
                    elif 'type' in item and item['type'] == 'data' and 'data' in item:
                         parts.append(DataPart(**item))
                    # NEW: Handle artifact reference (specific dict structure)
                    elif 'artifact-file-id' in item:
                         try:
                              file_id = item['artifact-file-id']
                              print(f"[DEBUG] Loading artifact file: {file_id}")
                              # Load artifact bytes using the service
                              adk_file_part = self._artifact_service.load_artifact(
                                   user_id=self.user_id,
                                   session_id=conversation_id,
                                   app_name=self.app_name,
                                   filename=file_id
                              )
                              # Assuming load_artifact returns an ADK Part with inline_data
                              if adk_file_part and adk_file_part.inline_data:
                                   file_bytes = adk_file_part.inline_data.data
                                   mime_type = adk_file_part.inline_data.mime_type
                                   # Encode bytes as base64 for our FilePart
                                   base64_data = base64.b64encode(file_bytes).decode('utf-8')
                                   parts.append(FilePart(
                                        file=FileContent(
                                             bytes=base64_data,
                                             mimeType=mime_type,
                                             name=file_id # Use file ID as name
                                        )
                                   ))
                              else:
                                   print(f"[WARN] Failed to load or get inline_data for artifact {file_id}.")
                                   parts.append(DataPart(data=item)) # Fallback
                         except Exception as artifact_e:
                              print(f"[ERROR] Failed to load artifact {item.get('artifact-file-id')}: {artifact_e}")
                              parts.append(DataPart(data=item)) # Fallback
                    else:
                         # Treat as generic data
                         parts.append(DataPart(data=item))
                elif isinstance(item, (int, float, bool)): # Handle primitives
                     parts.append(TextPart(text=str(item)))
                # else: # Handle other unexpected types in results
                #      print(f"[WARN] Unexpected item type in function response result: {type(item)}")
                #      parts.append(TextPart(text=str(item))) # Fallback to string representation

        except Exception as e:
            print(f"[ERROR] Failed to process function response result: {e}")
            traceback.print_exc()
            # Fallback: include the raw function response data
            parts.append(DataPart(data=part.function_response.model_dump()))
        return parts


# --- Helper Functions --- outside the class ---

def get_message_id(m: Message | None) -> str | None:
    """Safely extracts message_id from message metadata."""
    if m and hasattr(m, 'metadata') and m.metadata and 'message_id' in m.metadata:
        return m.metadata['message_id']
    return None

def get_last_message_id(m: Message | None) -> str | None:
    """Safely extracts last_message_id from message metadata."""
    if m and hasattr(m, 'metadata') and m.metadata and 'last_message_id' in m.metadata:
        return m.metadata['last_message_id']
    return None

def get_conversation_id(
    t: (Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent | Message | None)
) -> str | None:
    """Safely extracts conversation_id from various object types' metadata."""
    if t and hasattr(t, 'metadata') and t.metadata and 'conversation_id' in t.metadata:
        return t.metadata['conversation_id']
    # Some objects might have sessionId instead
    if t and hasattr(t, 'sessionId') and t.sessionId:
         return t.sessionId
    return None

def task_still_open(task: Task | None) -> bool:
    """Checks if a task is in a state considered 'open' (not final)."""
    if not task or not task.status: return False
    return task.status.state in [
        TaskState.SUBMITTED, TaskState.WORKING, TaskState.INPUT_REQUIRED
    ]