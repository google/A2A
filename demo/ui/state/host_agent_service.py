import json
import logging  # Add logging
import os
import sys
import traceback
from typing import Any

from common.types import Message, Part, Task
from service.client.client import ConversationClient
from service.types import (Conversation, CreateConversationRequest, Event,
                           GetEventRequest, ListAgentRequest,
                           ListConversationRequest, ListMessageRequest,
                           ListTaskRequest, PendingMessageRequest,
                           RegisterAgentRequest, SendMessageRequest)

from .state import (AppState, SessionTask, StateConversation, StateEvent,
                    StateMessage, StateTask)

logger = logging.getLogger(__name__) # Add logger
logger.setLevel(logging.DEBUG)

server_url = 'http://localhost:12000'


async def ListConversations() -> list[Conversation]:
    client = ConversationClient(server_url)
    try:
        response = await client.list_conversation(ListConversationRequest())
        return response.result
    except Exception as e:
        print('Failed to list conversations: ', e)


async def SendMessage(message: Message) -> str | None:
    client = ConversationClient(server_url)
    try:
        response = await client.send_message(SendMessageRequest(params=message))
        return response.result
    except Exception as e:
        print('Failed to send message: ', e)


async def CreateConversation() -> Conversation:
    client = ConversationClient(server_url)
    try:
        response = await client.create_conversation(CreateConversationRequest())
        return response.result
    except Exception as e:
        print('Failed to create conversation', e)


async def ListRemoteAgents():
    client = ConversationClient(server_url)
    try:
        response = await client.list_agents(ListAgentRequest())
        return response.result
    except Exception as e:
        print('Failed to read agents', e)


async def AddRemoteAgent(path: str):
    client = ConversationClient(server_url)
    try:
        await client.register_agent(RegisterAgentRequest(params=path))
    except Exception as e:
        print('Failed to register the agent', e)


async def GetEvents() -> list[Event]:
    client = ConversationClient(server_url)
    try:
        response = await client.get_events(GetEventRequest())
        return response.result
    except Exception as e:
        print('Failed to get events', e)


async def GetProcessingMessages():
    client = ConversationClient(server_url)
    try:
        response = await client.get_pending_messages(PendingMessageRequest())
        return dict(response.result)
    except Exception as e:
        print('Error getting pending messages', e)


def GetMessageAliases():
    return {}


async def GetTasks():
    client = ConversationClient(server_url)
    try:
        response = await client.list_tasks(ListTaskRequest())
        return response.result
    except Exception as e:
        print('Failed to list tasks ', e)


async def ListMessages(conversation_id: str) -> list[Message]:
    client = ConversationClient(server_url)
    try:
        response = await client.list_messages(
            ListMessageRequest(params=conversation_id)
        )
        return response.result
    except Exception as e:
        print('Failed to list messages ', e)


async def UpdateAppState(state: AppState, conversation_id: str):
    """Update the app state."""
    try:
        if conversation_id:
            state.current_conversation_id = conversation_id
            messages = await ListMessages(conversation_id)
            if not messages:
                state.messages = []
            else:
                state.messages = [convert_message_to_state(x) for x in messages]
        conversations = await ListConversations()
        if not conversations:
            state.conversations = []
        else:
            state.conversations = [
                convert_conversation_to_state(x) for x in conversations
            ]

        state.task_list = []
        for task in await GetTasks():
            state.task_list.append(
                SessionTask(
                    context_id=extract_conversation_id(task),
                    task=convert_task_to_state(task),
                )
            )
        state.background_tasks = await GetProcessingMessages()
        state.message_aliases = GetMessageAliases()
    except Exception as e:
        print('Failed to update state: ', e)
        traceback.print_exc(file=sys.stdout)


async def UpdateApiKey(api_key: str):
    """Update the API key"""
    import httpx

    try:
        # Set the environment variable
        os.environ['GOOGLE_API_KEY'] = api_key

        # Call the update API endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{server_url}/api_key/update', json={'api_key': api_key}
            )
            response.raise_for_status()
        return True
    except Exception as e:
        print('Failed to update API key: ', e)
        return False


def convert_message_to_state(message: Message) -> StateMessage:
    if not message:
        return StateMessage()

    return StateMessage(
        message_id=message.messageId,
        context_id=message.contextId if message.contextId else '',
        task_id=message.taskId if message.taskId else '',
        role=message.role,
        content=extract_content(message.parts),
    )


def convert_message_to_state(message: Message) -> StateMessage:
    if not message:
        return StateMessage()

    return StateMessage(
        message_id=message.messageId,
        context_id=message.contextId if message.contextId else "",
        task_id=message.taskId if message.taskId else "",
        role=message.role,
        content=extract_content(message.parts),
    )


def convert_conversation_to_state(
    conversation: Conversation,
) -> StateConversation:
    return StateConversation(
        conversation_id=conversation.conversation_id,
        conversation_name=conversation.name,
        is_active=conversation.is_active,
        message_ids=[extract_message_id(x) for x in conversation.messages],
    )


def convert_task_to_state(task: Task) -> StateTask:
    logger.debug(f"UI: Converting Task to StateTask. Task ID: {task.id}, Task Status: {task.status.state}, Number of artifacts: {len(task.artifacts) if task.artifacts else 0}")
    if task.artifacts:
        for i, art in enumerate(task.artifacts):
            logger.debug(f"UI: Task {task.id}, Artifact {i}: Name='{art.name}', NumParts={len(art.parts)}")
            if art.parts: # Add check if art.parts is not None
                for j, p_part in enumerate(art.parts): # Renamed p to p_part to avoid conflict with outer scope if any
                    mime_type_info = 'N/A'
                    if p_part.type == 'file' and p_part.file:
                        mime_type_info = p_part.file.mimeType
                    logger.debug(f"UI: Task {task.id}, Artifact {i}, Part {j}: Type='{p_part.type}', MimeType (if file)='{mime_type_info}'")

    # Get the first message as the description
    message = task.history[0] if task.history else None
    # last_message = task.history[-1] # This logic was removed as it might prepend unrelated content to artifacts
    output = (
        [extract_content(a.parts) for a in task.artifacts]
        if task.artifacts
        else []
    )
    logger.debug(f"UI: 'output' for StateTask (ID: {task.id}) before creating StateTask: {output}")
    return StateTask(
        task_id=task.id,
        context_id=task.contextId,
        state=str(task.status.state),
        message=convert_message_to_state(message) if message else StateMessage(),
        artifacts=output,
    )


def convert_event_to_state(event: Event) -> StateEvent:
    return StateEvent(
        context_id=extract_message_conversation(event.content),
        actor=event.actor,
        role=event.content.role,
        id=event.id,
        content=extract_content(event.content.parts),
    )


def extract_content(
    message_parts: list[Part],
) -> list[tuple[str | dict[str, Any], str]]:
    parts = []
    if not message_parts:
        return []
    for p in message_parts:
        content_val = None
        mime_val = None
        if p.type == 'text':
            content_val = p.text
            mime_val = 'text/plain'
        elif p.type == 'file':
            if p.file.uri: # Prioritize URI
                content_val = p.file.uri
                mime_val = p.file.mimeType 
            elif p.file.bytes: 
                content_val = p.file.bytes 
                mime_val = p.file.mimeType 
            else:
                # This case means a FilePart has no URI and no Bytes.
                logger.warning(f"UI: FilePart has no URI and no Bytes. Part: {p.model_dump_json()}")
                content_val = "<empty_file_part>" 
                mime_val = p.file.mimeType # Still try to get mimeType if available, might be None

        elif p.type == 'data':
            try:
                jsonData = json.dumps(p.data)
                if 'type' in p.data and p.data['type'] == 'form':
                    content_val = p.data
                    mime_val = 'form'
                else:
                    content_val = jsonData
                    mime_val = 'application/json'
            except Exception as e:
                print('Failed to dump data', e)
                content_val = '<data_serialization_error>'
                mime_val = 'text/plain'
        
        if mime_val is None: 
            logger.warning(f"UI: Mime type was None for part type '{p.type}'. Part content snippet: {str(content_val)[:50]}. Defaulting to 'text/plain'. Full part: {p.model_dump_json()}")
            mime_val = 'text/plain'
        
        if content_val is None: 
            logger.warning(f"UI: Content value was None for part type '{p.type}' (mime: {mime_val}). Defaulting content to '<empty_content>'. Full part: {p.model_dump_json()}")
            content_val = "<empty_content>"
            
        parts.append((content_val, mime_val))
    return parts


def extract_message_id(message: Message) -> str:
    return message.messageId


def extract_message_conversation(message: Message) -> str:
    return message.contextId if message.contextId else ''


def extract_conversation_id(task: Task) -> str:
    if task.contextId:
        return task.contextId
    # Tries to find the first conversation id for the message in the task.
    if task.status.message and task.status.message.contextId:
        return task.status.message.contextId
    if not task.artifacts:
        return ''
    for a in task.artifacts:
        if a.contextId:
            return a.contextId
    return ''
