import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

# Minimal Agent Logic (from helloworld's agent_executor.py)
class MinimalAgent:
    """Minimal Agent Logic."""

    async def invoke(self) -> str:
        return 'Hello from Minimal A2A Agent!'

class MinimalAgentExecutor(AgentExecutor):
    """Minimal Agent Executor."""

    def __init__(self):
        self.agent = MinimalAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        result = await self.agent.invoke()
        event_queue.enqueue_event(new_agent_text_message(result))

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        # For a minimal agent, explicit cancellation might not be supported
        # or could be simplified. Raising an error or logging is an option.
        # Depending on DefaultRequestHandler, it might also handle this.
        # For true minimality, we can state it's not supported.
        raise NotImplementedError('Cancel operation is not supported by this minimal agent.')

if __name__ == '__main__':
    # Define the agent's skill
    minimal_skill = AgentSkill(
        id='minimal_echo',
        name='Minimal Echo Skill',
        description='Echoes a simple message from the agent.',
        tags=['minimal', 'echo'],
        examples=['ping', 'say hi'],
        inputModes=['text/plain'], # Optional: specify if different from agent default
        outputModes=['text/plain'], # Optional: specify if different from agent default
    )

    # Define the Agent Card
    agent_card = AgentCard(
        name='Minimal A2A Agent',
        description='A very basic A2A agent example for Ionverse.',
        url='http://localhost:8000/', # Adjusted port
        version='0.1.0',
        defaultInputModes=['text/plain'],
        defaultOutputModes=['text/plain'],
        capabilities=AgentCapabilities(streaming=True), # Retaining streaming capability
        skills=[minimal_skill],
        # No authentication for this minimal example
        # supportsAuthenticatedExtendedCard=False (or omit)
    )

    # Set up the request handler
    request_handler = DefaultRequestHandler(
        agent_executor=MinimalAgentExecutor(),
        task_store=InMemoryTaskStore(), # Simple in-memory store for tasks
    )

    # Create the A2A application
    server_app_builder = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
        # No extended_agent_card for minimal example
    )

    # Run the server with Uvicorn
    uvicorn.run(
        server_app_builder.build(),
        host='0.0.0.0',
        port=8000 # Adjusted port
    )
