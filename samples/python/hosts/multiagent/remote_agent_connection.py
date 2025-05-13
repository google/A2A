import uuid
from typing import Callable
from common.client import A2AClient
from common.types import (
    A2AClientError,
    AgentCard,
    Message,
    MessageSendParams,
    Task,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    TextPart,
)


TaskCallbackArg = Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent
TaskUpdateCallback = Callable[[TaskCallbackArg, AgentCard], Task]


class RemoteAgentConnections:
    """A class to hold the connections to the remote agents."""

    def __init__(self, agent_card: AgentCard):
        self.agent_client = A2AClient(agent_card)
        self.card = agent_card

        self.conversation_name = None
        self.conversation = None
        self.pending_tasks = set()

    def get_agent(self) -> AgentCard:
        return self.card

    async def send_message(
        self,
        request: MessageSendParams,
        task_callback: TaskUpdateCallback | None,
    ) -> Task | Message | None:
        try:
            if self.card.capabilities.streaming:
                task = None
                async for response in self.agent_client.send_message_stream(
                    request.model_dump()
                ):
                    if not response.result:
                        return response.error
                    # In the case a message is returned, that is the end of the interaction.
                    if isinstance(response.result, Message):
                        return response

                    # Otherwise we are in the Task + TaskUpdate cycle.
                    if task_callback and response.result:
                        task = task_callback(response.result, self.card)
                    if hasattr(response.result, 'final') and response.result.final:
                        break
                return task
            else:  # Non-streaming
                response = await self.agent_client.send_message(
                    request.model_dump()
                )
                if isinstance(response.result, Message):
                    return response.result

                if task_callback:
                    task_callback(response.result, self.card)
                return response.result
        except A2AClientError as e:
            return Message(
                role='agent',
                parts=[
                    TextPart(text=e.data['hint'] if e.status_code in (401, 403) else str(e)),
                ],
                messageId=str(uuid.uuid4()),
                metadata=e.data,
            )
