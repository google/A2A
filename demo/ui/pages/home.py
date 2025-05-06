import mesop as me

from components.conversation_list import conversation_list
from components.header import header
from state.state import AppState


@me.stateclass
class PageState:
    """Local Page State"""

    temp_name: str = ''


def on_blur_set_name(e: me.InputBlurEvent):
    """Input handler"""
    state = me.state(PageState)
    state.temp_name = e.value


def on_enter_change_name(e: me.components.input.input.InputEnterEvent):  # pylint: disable=unused-argument
    """Change name button handler"""
    state = me.state(PageState)
    app_state = me.state(AppState)
    app_state.name = state.temp_name
    app_state.greeting = ''  # reset greeting
    yield


def on_click_change_name(e: me.ClickEvent):  # pylint: disable=unused-argument
    """Change name button handler"""
    state = me.state(PageState)
    app_state = me.state(AppState)
    app_state.name = state.temp_name
    app_state.greeting = ''  # reset greeting
    yield


def home_page_content(app_state: AppState):
    """Home Page"""
    with me.box(
        style=me.Style(
            display='flex',
            flex_direction='column',
            height='100%',
        ),
    ):
        with me.box(
            style=me.Style(
                background=me.theme_var('background'),
                height='100%',
                margin=me.Margin(bottom=20),
            )
        ):
            with me.box(
                style=me.Style(
                    background=me.theme_var('background'),
                    padding=me.Padding(top=24, left=24, right=24, bottom=24),
                    display='flex',
                    flex_direction='column',
                    width='100%',
                )
            ):
                with header('Conversations', 'message'):
                    pass
                conversation_list(app_state.conversations)
