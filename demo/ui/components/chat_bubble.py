import mesop as me
from state.state import AppState, StateMessage


# Helper function to render individual message content parts (text, image, video)
def _render_message_part(
    content: str,
    media_type: str,
    role: str,
    key: str,
):
    """Render a single part of a message (text, image, video) with bubble styling."""
    bubble_style = me.Style(
        padding=me.Padding(top=8, left=15, right=15, bottom=8),
        margin=me.Margin(top=2, bottom=2),
        background=(
            me.theme_var('primary-container')
            if role == 'user'
            else me.theme_var('secondary-container')
        ),
        border_radius=15,
        box_shadow=(
            '0 1px 2px 0 rgba(60, 64, 67, 0.3), '
            '0 1px 3px 1px rgba(60, 64, 67, 0.15)'
        ),
        max_width='75%',
        word_wrap='break-word',
    )

    with me.box(style=bubble_style, key=key):
        if media_type == 'image/png':
            if '/message/file' not in content:
                content = 'data:image/png;base64,' + content
            me.image(
                src=content,
                style=me.Style(
                    max_width='100%',  
                    height='auto',
                    border_radius=10,  
                    display='block',
                ),
            )
        elif media_type and media_type.startswith('video/'):  # Handle video/mp4, video/webm, etc.
            # Check if the content is a string and looks like a URL or GCS URI
            if isinstance(content, str) and (content.startswith('http://') or content.startswith('https://') or content.startswith('gs://')):
                me.video(
                    src=content,  # Use the URI as the source
                    style=me.Style(
                        width='100%',  # Video responsive within the bubble
                        max_width='480px',  # Max width for video elements
                        border_radius=10,
                        display='block',
                    ),
                )
            else:
                # Fallback if content is not a valid URL for video
                # This might happen if the FilePart had bytes but no URI,
                # and extract_content put the bytes (or default) here.
                # Or if mimeType was video but content was None.
                me.markdown(
                    f"Video content (type: {media_type}) could not be displayed. Content snippet: {str(content)[:100]}...",
                    style=me.Style(font_family='Google Sans'),
                )
        else:  # Default to markdown for text/plain, application/json, etc.
            me.markdown(
                content,
                style=me.Style(font_family='Google Sans'),
            )


# Helper function to render the progress indicator for a message
def _render_message_progress(progress_text: str, role: str, key: str):
    """Renders a progress indicator bubble for a message."""
    progress_bubble_style = me.Style(
        padding=me.Padding(top=8, left=15, right=15, bottom=8),
        margin=me.Margin(top=5),
        background=me.theme_var('surface-variant'), # Distinct background for progress
        border_radius=15,
        box_shadow=(
            '0 1px 2px 0 rgba(60, 64, 67, 0.3), '
            '0 1px 3px 1px rgba(60, 64, 67, 0.15)'
        ),
        max_width='75%',
        font_family='Google Sans',
    )
    with me.box(style=progress_bubble_style, key=key):
        me.text(
            progress_text,
            style=me.Style(padding=me.Padding(bottom=5)),
        )
        me.progress_bar(color='accent')


@me.component
def chat_bubble(message: StateMessage, key: str):
    """Chat bubble component. Key should be message.message_id."""
    app_state = me.state(AppState)

    if not message.content:
        # If there's no content, but it's a pending task, we might still show progress.
        # This case can be refined if needed. For now, requires content to render bubble.
        print(f'No message content for message_id: {message.message_id}')

    # Main container for the entire message (all parts + progress bar)
    # Aligns the whole message to the left (agent) or right (user)
    with me.box(
        style=me.Style(
            display='flex',
            flex_direction='column',
            align_items='flex-start' if message.role == 'agent' else 'flex-end',
            width='100%', # Take full width to allow alignment
            margin=me.Margin(bottom=10), # Space between messages
        ),
    ):
        # Render each part of the message content
        for idx, pair in enumerate(message.content):
            content_data, media_type = pair
            part_key = f"{key}_part_{idx}"  # Unique key for each message part
            _render_message_part(content_data, media_type, message.role, part_key)

        # Render progress bar for the entire message if it's a background task
        show_progress_bar = (
            message.message_id in app_state.background_tasks
            or message.message_id in app_state.message_aliases.values()
        )
        if show_progress_bar:
            progress_text = app_state.background_tasks.get(message.message_id)
            # Ensure progress_text is a string, default to 'Working...'
            if not isinstance(progress_text, str) or not progress_text.strip():
                progress_text = 'Working...'
            progress_bar_key = f"{key}_progress" # Unique key for the progress bar
            _render_message_progress(progress_text, message.role, progress_bar_key)
