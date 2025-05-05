import uuid

import mesop as me

from common.types import Message, TextPart
from state.host_agent_service import (
    ListConversations,
    SendMessage,
    convert_message_to_state,
)
from state.state import AppState, SettingsState, StateMessage

from .chat_bubble import chat_bubble
from .form_render import form_sent, is_form, render_form


@me.stateclass
class PageState:
    """Local Page State"""

    conversation_id: str = ''
    message_content: str = ''


def on_blur(e: me.InputBlurEvent):
    """Input handler"""
    state = me.state(PageState)
    state.message_content = e.value


async def send_message(message: str, message_id: str = ''):
    state = me.state(PageState)
    app_state = me.state(AppState)
    settings_state = me.state(SettingsState)
    c = next(
        (
            x
            for x in await ListConversations()
            if x.conversation_id == state.conversation_id
        ),
        None,
    )
    if not c:
        print('Conversation id ', state.conversation_id, ' not found')
    request = Message(
        id=message_id,
        role='user',
        parts=[TextPart(text=message)],
        metadata={
            'conversation_id': c.conversation_id if c else '',
            'conversation_name': c.name if c else '',
        },
    )
    # Add message to state until refresh replaces it.
    state_message = convert_message_to_state(request)
    if not app_state.messages:
        app_state.messages = []
    app_state.messages.append(state_message)
    conversation = next(
        filter(
            lambda x: x.conversation_id == c.conversation_id,
            app_state.conversations,
        ),
        None,
    )
    if conversation:
        conversation.message_ids.append(state_message.message_id)
    response = await SendMessage(request)


async def send_message_enter(e: me.InputEnterEvent):  # pylint: disable=unused-argument
    """Send message handler"""
    yield
    state = me.state(PageState)
    state.message_content = e.value
    app_state = me.state(AppState)
    message_id = str(uuid.uuid4())
    app_state.background_tasks[message_id] = ''
    yield
    await send_message(state.message_content, message_id)
    yield


async def send_message_button(e: me.ClickEvent):  # pylint: disable=unused-argument
    """Send message button handler"""
    yield
    state = me.state(PageState)
    app_state = me.state(AppState)
    message_id = str(uuid.uuid4())
    app_state.background_tasks[message_id] = ''
    await send_message(state.message_content, message_id)
    yield


@me.component
def conversation():
    """Conversation component"""
    page_state = me.state(PageState)
    app_state = me.state(AppState)
    if 'conversation_id' in me.query_params:
        page_state.conversation_id = me.query_params['conversation_id']
        app_state.current_conversation_id = page_state.conversation_id
    with me.box(
        style=me.Style(
            display='flex',
            justify_content='space-between',
            flex_direction='column',
        )
    ):
        for message in app_state.messages:
            if is_form(message):
                render_form(message, app_state)
            elif form_sent(message, app_state):
                chat_bubble(
                    StateMessage(
                        message_id=message.message_id,
                        role=message.role,
                        content=[('Form submitted', 'text/plain')],
                    ),
                    message.message_id,
                )
            else:
                chat_bubble(message, message.message_id)

        with me.box(
            style=me.Style(
                display='flex',
                flex_direction='row',
                gap=5,
                align_items='center',
                min_width=500,
                width='100%',
            )
        ):
            me.input(
                label='How can I help you?',
                on_blur=on_blur,
                on_enter=send_message_enter,
                style=me.Style(min_width='80vw'),
            )
            with me.content_button(
                type='flat',
                on_click=send_message_button,
            ):
                me.icon(icon='send')
