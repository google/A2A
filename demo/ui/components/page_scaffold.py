import mesop as me
import mesop.labs as mel

from state.host_agent_service import UpdateAppState
from state.state import AppState
from styles.styles import (
    MAIN_COLUMN_STYLE,
    PAGE_BACKGROUND_PADDING_STYLE,
    PAGE_BACKGROUND_STYLE,
    SIDENAV_MAX_WIDTH,
    SIDENAV_MIN_WIDTH,
)

from .async_poller import AsyncAction, async_poller
from .side_nav import sidenav


async def refresh_app_state(e: mel.WebEvent):  # pylint: disable=unused-argument
    """Refresh app state event handler"""
    yield
    app_state = me.state(AppState)
    await UpdateAppState(app_state, app_state.current_conversation_id)
    yield


@me.content_component
def page_scaffold():
    """Page scaffold component"""
    app_state = me.state(AppState)
    action = (
        AsyncAction(
            value=app_state, duration_seconds=app_state.polling_interval
        )
        if app_state
        else None
    )
    async_poller(action=action, trigger_event=refresh_app_state)

    sidenav('')

    with me.box(
        style=me.Style(
            display='flex',
            flex_direction='column',
            height='100%',
            margin=me.Margin(
                left=SIDENAV_MAX_WIDTH
                if app_state.sidenav_open
                else SIDENAV_MIN_WIDTH,
            ),
        ),
    ):
        with me.box(
            style=me.Style(
                background=me.theme_var('background'),
                height='100%',
                overflow_y='scroll',
                margin=me.Margin(bottom=20),
            )
        ):
            me.slot()


@me.content_component
def page_frame():
    """Page Frame"""
    with me.box(style=MAIN_COLUMN_STYLE):
        with me.box(style=PAGE_BACKGROUND_STYLE):
            with me.box(style=PAGE_BACKGROUND_PADDING_STYLE):
                me.slot()
