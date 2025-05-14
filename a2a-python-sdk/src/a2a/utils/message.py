import uuid

from a2a.types import (
    Message,
    Part,
    Role,
    TextPart,
)


def new_agent_text_message(
    text: str, context_id: str | None = None, task_id: str | None = None
) -> Message:
    """Creates a new agent text message."""
    return Message(
        role=Role.agent,
        parts=[Part(root=TextPart(text=text))],
        messageId=str(uuid.uuid4()),
        taskId=task_id,
        contextId=context_id,
    )


def get_text_parts(parts: list[Part]) -> list[str]:
    """Return all text parts from a list of parts."""
    return [part.root.text for part in parts if isinstance(part.root, TextPart)]


def get_message_text(message: Message, delimiter='\n') -> str:
    return delimiter.join(get_text_parts(message.parts))
