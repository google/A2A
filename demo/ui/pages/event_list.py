import stat

import mesop as me

from components.header import header
from components.page_scaffold import page_scaffold
from components.page_scaffold import page_frame
from components.event_viewer import event_list
from state.state import AppState
from state.agent_state import AgentState


def event_list_page(app_state: AppState):
    """Agents List Page"""
    state = me.state(AgentState)
    with page_scaffold():  # pylint: disable=not-context-manager
        with page_frame():
            with header('Event List', 'list'):
                pass
            event_list()
