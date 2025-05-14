import click

from agent_executor import HelloWorldAgentExecutor

from a2a.server import A2AServer
from a2a.server.request_handlers import DefaultA2ARequestHandler
from a2a.types import (
    AgentAuthentication,
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)


@click.command()
@click.option('--host', 'host', default='localhost')
@click.option('--port', 'port', default=9999)
def main(host: str, port: int):
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
        url='http://localhost:9999/',
        version='1.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=AgentCapabilities(),
        skills=[skill],
        authentication=AgentAuthentication(schemes=['public']),
    )

    request_handler = DefaultA2ARequestHandler(
        agent_executor=HelloWorldAgentExecutor()
    )

    server = A2AServer(agent_card=agent_card, request_handler=request_handler)
    server.start(host=host, port=port)


if __name__ == '__main__':
    main()
