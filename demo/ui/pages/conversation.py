import mesop as me

from components.header import header
from components.page_scaffold import page_scaffold
from components.page_scaffold import page_frame
from components.conversation import conversation
from state.state import AppState


def conversation_page(app_state: AppState):
    """Conversation Page"""
    state = me.state(AppState)
    with page_scaffold():  # pylint: disable=not-context-manager
        with page_frame():
            with header('Conversation', 'chat'):
                pass
            conversation()
