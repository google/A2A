import mesop as me

from state.state import AppState, StateMessage


@me.component
def chat_bubble(message: StateMessage, key: str):
    """Chat bubble component"""
    app_state = me.state(AppState)
    show_progress_bar = (
        message.message_id in app_state.background_tasks
        or message.message_id in app_state.message_aliases.values()
    )
    progress_text = ''
    if show_progress_bar:
        progress_text = app_state.background_tasks[message.message_id]
    if not message.content:
        print('No message content')
    for pair in message.content:
        chat_box(
            pair[0],
            pair[1],
            message.role,
            key,
            progress_bar=show_progress_bar,
            progress_text=progress_text,
        )


def chat_box(
    content: str,
    media_type: str,
    role: str,
    key: str,
    progress_bar: bool,
    progress_text: str,
):
    with me.box(
        style=me.Style(
            display='flex',
            justify_content=('space-between' if role == 'agent' else 'end'),
            min_width=500,
        ),
        key=key,
    ):
        with me.box(
            style=me.Style(display='flex', flex_direction='column', gap=5)
        ):
            if media_type == 'image/png':
                if '/message/file' not in content:
                    content = 'data:image/png;base64,' + content
                me.image(
                    src=content,
                    style=me.Style(
                        width='50%',
                        object_fit='contain',
                    ),
                )
            else:
                me.markdown(
                    content,
                    style=me.Style(
                        font_family='Google Sans',
                        box_shadow=(
                            '0 1px 2px 0 rgba(60, 64, 67, 0.3), '
                            '0 1px 3px 1px rgba(60, 64, 67, 0.15)'
                        ),
                        padding=me.Padding(top=1, left=15, right=15, bottom=1),
                        margin=me.Margin(top=5, left=0, right=0, bottom=5),
                        background=(
                            me.theme_var('primary-container')
                            if role == 'user'
                            else me.theme_var('secondary-container')
                        ),
                        border_radius=15,
                    ),
                )
    if progress_bar:
        with me.box(
            style=me.Style(
                display='flex',
                justify_content=('space-between' if role == 'user' else 'end'),
                min_width=500,
            ),
            key=key,
        ):
            with me.box(
                style=me.Style(display='flex', flex_direction='column', gap=5)
            ):
                with me.box(
                    style=me.Style(
                        font_family='Google Sans',
                        box_shadow=(
                            '0 1px 2px 0 rgba(60, 64, 67, 0.3), '
                            '0 1px 3px 1px rgba(60, 64, 67, 0.15)'
                        ),
                        padding=me.Padding(top=1, left=15, right=15, bottom=1),
                        margin=me.Margin(top=5, left=0, right=0, bottom=5),
                        background=(
                            me.theme_var('primary-container')
                            if role == 'agent'
                            else me.theme_var('secondary-container')
                        ),
                        border_radius=15,
                    ),
                ):
                    if not progress_text:
                        progress_text = 'Working...'
                    me.text(
                        progress_text,
                        style=me.Style(
                            padding=me.Padding(
                                top=1, left=15, right=15, bottom=1
                            ),
                            margin=me.Margin(top=5, left=0, right=0, bottom=5),
                        ),
                    )
                    me.progress_bar(color='accent')
