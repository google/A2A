import mesop as me
import mesop.labs as mel

import asyncio
import uuid
import functools
import threading
import httpx  # << NEW: import for sending HTTP requests

from state.host_agent_service import pick_agent_using_chatgpt
from state.state import AppState, SettingsState, StateMessage
from state.host_agent_service import SendMessage, ListConversations, convert_message_to_state
from .chat_bubble import chat_bubble
from .form_render import is_form, render_form, form_sent
from .async_poller import async_poller, AsyncAction
from common.types import Message, TextPart

@me.stateclass
class PageState:
    """Local Page State"""
    conversation_id: str = ""
    message_content: str = ""

def on_blur(e: me.InputBlurEvent):
    """Input handler for text field blur."""
    state = me.state(PageState)
    state.message_content = e.value

async def send_message(message: str, message_id: str = ""):
    """Sends the user message to the backend for processing."""
    state = me.state(PageState)
    app_state = me.state(AppState)
    # settings_state = me.state(SettingsState) # Not currently used

    # --- 1. Find the relevant conversation state (local is usually sufficient) ---
    # Use the local app_state.conversations as the primary source for UI logic
    conversation_state = next(
        (conv for conv in app_state.conversations if conv.conversation_id == state.conversation_id),
        None,
    )

    if not conversation_state:
        # As a fallback, check the server list in case the local state is lagging
        server_conversations = await ListConversations()
        server_conv_data = next(
            (c for c in server_conversations if c.conversation_id == state.conversation_id),
            None,
        )
        if server_conv_data:
             print(f"[WARN] Conversation {state.conversation_id} found on server but not in local app_state. Using server data.")
             # You might want to update local app_state here if needed, or just use server_conv_data attributes
             conv_id_to_use = server_conv_data.conversation_id
             conv_name_to_use = getattr(server_conv_data, 'name', 'Unknown Conversation')
             # Try to get remote_agent_url if available from server data too
             remote_agent_url = getattr(server_conv_data, "remote_agent_url", None)
        else:
            print(f"[ERROR] Conversation {state.conversation_id} not found locally or on server. Cannot send message.")
            return
    else:
        # Use data from the found local conversation state
        conv_id_to_use = conversation_state.conversation_id
        conv_name_to_use = conversation_state.conversation_name
        remote_agent_url = getattr(conversation_state, "remote_agent_url", None)


    # --- 2. Append User Message Locally (Immediate UI Feedback) ---
    user_state_message = StateMessage(
        message_id=message_id, # Use the UUID generated before calling send_message
        role="user",
        content=[(message, "text/plain")],
        metadata={"conversation_id": conv_id_to_use} # Essential for UI filtering
    )
    if not app_state.messages:
        app_state.messages = []
    # Add only if it doesn't exist (prevents duplicates on rapid clicks/enters)
    if not any(msg.message_id == message_id for msg in app_state.messages):
        app_state.messages.append(user_state_message)
        # Also update the message_ids list in the local conversation object
        if conversation_state and message_id not in conversation_state.message_ids:
             conversation_state.message_ids.append(message_id)

    # --- 3. Prepare Metadata for Backend ---
    request_metadata = {
        'conversation_id': conv_id_to_use,
        'conversation_name': conv_name_to_use,
        # Add any other relevant context if needed
    }

    # --- 4. Determine Target Agent and Add to Metadata (if needed) ---
    if not remote_agent_url:
        print(f"[DEBUG] No remote_agent_url set for conversation {conv_id_to_use}. Attempting to pick one.")
        try:
            # Assuming pick_agent_using_chatgpt is async
            suggested_agent = await pick_agent_using_chatgpt(message)
            if suggested_agent:
                remote_agent_url = suggested_agent
                print(f"[DEBUG] ChatGPT suggested agent: {remote_agent_url}")
                # Store it back into the local conversation state for persistence within the session
                if conversation_state:
                    conversation_state.remote_agent_url = remote_agent_url
                # IMPORTANT: Add the chosen URL to metadata for the backend
                request_metadata['remote_agent_url'] = remote_agent_url
            else:
                print("[INFO] No specific agent picked by router. Backend will use default.")
        except Exception as e:
             print(f"[ERROR] Failed to pick agent using ChatGPT: {e}")
             # Proceed without a specific agent URL
    else:
        # If an agent URL was already known locally, pass it to the backend
        print(f"[DEBUG] Using existing remote_agent_url: {remote_agent_url}")
        request_metadata['remote_agent_url'] = remote_agent_url

    # --- 5. Create the Message Payload for the Backend ---
    backend_request = Message(
        # Let backend assign the canonical ID via sanitize_message
        role="user",
        parts=[TextPart(text=message)],
        metadata=request_metadata,
    )

    # --- 6. Send the Request to the Backend ---
    print(f"Sending message content to backend via SendMessage for conversation {conv_id_to_use}.")
    try:
        await SendMessage(backend_request)
        print(f"SendMessage call completed for conversation {conv_id_to_use}.")
    except Exception as e:
        print(f"[ERROR] Failed to send message via SendMessage: {e}")
        # Optionally, update UI to show an error state?

    # NOTE: No handling of the AI response here. That will happen when the
    # async_poller calls UpdateAppState, which fetches the updated message
    # list (including the AI response added by the backend) from the server

async def send_message_enter(e: me.InputEnterEvent):
    """Send message on Enter key."""
    state = me.state(PageState)
    app_state = me.state(AppState)
    message_id = str(uuid.uuid4())
    app_state.background_tasks[message_id] = ""

    await send_message(state.message_content, message_id)
    yield

async def send_message_button(e: me.ClickEvent):
    """Send message on Send button."""
    yield
    state = me.state(PageState)
    app_state = me.state(AppState)
    message_id = str(uuid.uuid4())
    app_state.background_tasks[message_id] = ""
    await send_message(state.message_content, message_id)
    yield

@me.component
def conversation():
    """Conversation component."""
    page_state = me.state(PageState)
    app_state = me.state(AppState)

    print(f"Current conversation ID: {page_state.conversation_id}")
    print(f"App state current conversation ID: {app_state.current_conversation_id}")
    print(f"Message count: {len(app_state.messages)}")

    # Log each message's conversation ID
    for msg in app_state.messages:
        msg_conv_id = None
        if hasattr(msg, "metadata") and isinstance(msg.metadata, dict):
            msg_conv_id = msg.metadata.get("conversation_id")
        print(f"Message ID: {msg.message_id}, Conv ID: {msg_conv_id}")

    if "conversation_id" in me.query_params:
        page_state.conversation_id = me.query_params["conversation_id"]
        app_state.current_conversation_id = page_state.conversation_id
    
    current_conversation_id = page_state.conversation_id
    
    with me.box(
        style=me.Style(
            display="flex",
            justify_content="space-between",
            flex_direction="column",
        )
    ):
        # 🛠 FIX: ONLY SHOW MESSAGES for current conversation
        for message in app_state.messages:
            # check metadata or fallback
            message_conversation_id = None
            if hasattr(message, "metadata") and isinstance(message.metadata, dict):
                message_conversation_id = message.metadata.get("conversation_id")
            
            # if no metadata, try to infer
            if not message_conversation_id:
                message_conversation_id = app_state.current_conversation_id  # fallback

            if message_conversation_id != current_conversation_id:
                continue  # skip unrelated messages!

            if is_form(message):
                render_form(message, app_state)
            elif form_sent(message, app_state):
                chat_bubble(StateMessage(
                    message_id=message.message_id,
                    role=message.role,
                    content=[("Form submitted", "text/plain")]
                ), message.message_id)
            else:
                chat_bubble(message, message.message_id)

        # input + send button...
        with me.box(
            style=me.Style(
                display="flex",
                flex_direction="row",
                gap=5,
                align_items="center",
                min_width=500,
                width="100%",
            )
        ):
            me.input(
                label="How can I help you?",
                on_blur=on_blur,
                on_enter=send_message_enter,
                style=me.Style(min_width="80vw"),
            )
            with me.content_button(
                type="flat",
                on_click=send_message_button,
            ):
                me.icon(icon="send")