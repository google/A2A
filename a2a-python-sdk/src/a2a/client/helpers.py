from uuid import uuid4

from a2a.types import Message, Part, Role, TextPart


def create_text_message_object(
    role: Role = Role.user, content: str = ''
) -> Message:
    """Create a Message object for the given role and content."""
    return Message(
        role=role, parts=[Part(TextPart(text=content))], messageId=str(uuid4())
    )
