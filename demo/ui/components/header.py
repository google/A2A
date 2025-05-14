import mesop as me

from .poller import polling_buttons


@me.content_component
def header(title: str, icon: str):
    """Header component"""
    with me.box(
        style=me.Style(
            display='flex',
            justify_content='space-between',
        )
    ):
        with me.box(
            style=me.Style(display='flex', flex_direction='row', gap=5)
        ):
            me.icon(icon=icon)
            me.text(
                title,
                type='headline-5',
                style=me.Style(font_family='Google Sans'),
            )
        me.slot()
        polling_buttons()
