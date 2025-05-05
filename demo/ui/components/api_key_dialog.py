import os

import mesop as me

from state.host_agent_service import UpdateApiKey
from state.state import AppState

from .dialog import dialog, dialog_actions


def on_api_key_change(e: me.InputBlurEvent):
    """Save API key to app state when input changes"""
    state = me.state(AppState)
    state.api_key = e.value


async def save_api_key(e: me.ClickEvent):
    """Save API key and close dialog"""
    yield  # Yield to allow UI update

    state = me.state(AppState)

    # Validate API key is not empty
    if not state.api_key.strip():
        return

    # Set the environment variable for current process
    os.environ['GOOGLE_API_KEY'] = state.api_key

    # Update the API key in the server
    await UpdateApiKey(state.api_key)

    state.api_key_dialog_open = False

    yield


@me.component
def api_key_dialog():
    """Dialog for API key input"""
    state = me.state(AppState)

    with dialog(state.api_key_dialog_open):
        with me.box(
            style=me.Style(display='flex', flex_direction='column', gap=12)
        ):
            me.text(
                'Google API Key Required',
                type='headline-4',
                style=me.Style(margin=me.Margin(bottom=10)),
            )
            me.text(
                'Please enter your Google API Key to use the application.',
                style=me.Style(margin=me.Margin(bottom=20)),
            )
            me.input(
                label='Google API Key',
                value=state.api_key,
                on_blur=on_api_key_change,
                type='password',
                style=me.Style(width='100%'),
            )

        with dialog_actions():
            me.button('Save', on_click=save_api_key)
