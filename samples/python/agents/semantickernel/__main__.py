import logging

import click
import httpx

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, InMemoryPushNotifier
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from agent_executor import SemanticKernelTravelAgentExecutor
from common.types import AgentCapabilities, AgentCard, AgentSkill
from dotenv import load_dotenv


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


@click.command()
@click.option('--host', default='localhost')
@click.option('--port', default=10020)
def main(host, port):
    """Starts the Semantic Kernel Agent server using A2A."""
    httpx_client = httpx.AsyncClient()
    request_handler = DefaultRequestHandler(
        agent_executor=SemanticKernelTravelAgentExecutor(),
        task_store=InMemoryTaskStore(),
        push_notifier=InMemoryPushNotifier(httpx_client),
    )

    server = A2AStarletteApplication(
        agent_card=get_agent_card(host, port), http_handler=request_handler
    )
    import uvicorn

    uvicorn.run(server.build(), host=host, port=port)


def get_agent_card(host: str, port: int):
    """Returns the Agent Card for the Semantic Kernel Travel Agent."""

    # Build the agent card
    capabilities = AgentCapabilities(streaming=True)
    skill_trip_planning = AgentSkill(
        id='trip_planning_sk',
        name='Semantic Kernel Trip Planning',
        description=(
            'Handles comprehensive trip planning, including currency exchanges, itinerary creation, sightseeing, '
            'dining recommendations, and event bookings using Frankfurter API for currency conversions.'
        ),
        tags=['trip', 'planning', 'travel', 'currency', 'semantic-kernel'],
        examples=[
            'Plan a budget-friendly day trip to Seoul including currency exchange.',
            "What's the exchange rate and recommended itinerary for visiting Tokyo?",
        ],
    )

    agent_card = AgentCard(
        name='SK Travel Agent',
        description=(
            'Semantic Kernel-based travel agent providing comprehensive trip planning services '
            'including currency exchange and personalized activity planning.'
        ),
        url=f'http://{host}:{port}/',
        version='1.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=capabilities,
        skills=[skill_trip_planning],
    )

    return agent_card


if __name__ == '__main__':
    main()
