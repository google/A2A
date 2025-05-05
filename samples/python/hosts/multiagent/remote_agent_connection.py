from typing import Callable
from common.types import (
    AgentCard,
    Task,
    Message,
    MessageSendParams,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
)
from common.client import A2AClient

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
    if self.card.capabilities.streaming:
      task = None
      async for response in self.agent_client.send_message_stream(request.model_dump()):
        # In the case a message is returned, that is the end of the interaction.
        if isinstance(response.result, Message):
          return response

        # Otherwise we are in the Task + TaskUpdate cycle.
        if task_callback and response.result:
          task = task_callback(response.result, self.card)
        if hasattr(response.result, 'final') and response.result.final:
          break
        if not response.result:
          return response.error
      return task
    else: # Non-streaming
      response = await self.agent_client.send_message(request.model_dump())
      if isinstance(response.result, Message):
        return response.result

      if task_callback:
        task_callback(response.result, self.card)
      return response.result
