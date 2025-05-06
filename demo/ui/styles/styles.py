import mesop as me


SIDENAV_MIN_WIDTH = 68
SIDENAV_MAX_WIDTH = 200

DEFAULT_MENU_STYLE = me.Style(align_content='left')

_FANCY_TEXT_GRADIENT = me.Style(
    color='transparent',
    background=(
        'linear-gradient(72.83deg,#4285f4 11.63%,#9b72cb 40.43%,#d96570 68.07%)'
        ' text'
    ),
)

MAIN_COLUMN_STYLE = me.Style(
    display='flex',
    flex_direction='column',
    height='100%',
)

PAGE_BACKGROUND_STYLE = me.Style(
    background=me.theme_var('background'),
    height='100%',
    overflow_y='scroll',
    margin=me.Margin(bottom=20),
)

PAGE_BACKGROUND_PADDING_STYLE = me.Style(
    background=me.theme_var('background'),
    padding=me.Padding(top=24, left=24, right=24, bottom=24),
    display='flex',
    flex_direction='column',
)
