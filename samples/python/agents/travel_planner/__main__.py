from agent_executor import TravelPlannerAgentExecutor

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentAuthentication,
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)


if __name__ == '__main__':

    skill = AgentSkill(
        id='travel_planner',
        name='travel planner agent',
        description='travel planner',
        tags=['travel planner'],
        examples=['hello', 'nice to meet you!'],
    )

    agent_card = AgentCard(
        name='travel planner Agent',
        description='travel planner',
        url='http://localhost:10001/',
        version='1.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
        authentication=AgentAuthentication(schemes=['public']),
    )


    request_handler = DefaultRequestHandler(
        agent_executor=TravelPlannerAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )
    import uvicorn

    uvicorn.run(server.build(), host='0.0.0.0', port=10001)
