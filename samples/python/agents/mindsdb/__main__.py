import os
import sys

import click

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from agent import MindsDBAgent  # type: ignore[import-untyped]
from agent_executor import MindsDBAgentExecutor  # type: ignore[import-untyped]
from dotenv import load_dotenv


load_dotenv()


@click.command()
@click.option('--host', default='localhost')
@click.option('--port', default=10006)
def main(host, port):
    if not os.getenv('MINDS_API_KEY'):
        print('MINDS_API_KEY environment variable not set.')
        sys.exit(1)

    request_handler = DefaultRequestHandler(
        agent_executor=MindsDBAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=get_agent_card(host, port), http_handler=request_handler
    )
    import uvicorn

    uvicorn.run(server.build(), host=host, port=port)


def get_agent_card(host: str, port: int):
    """Returns the Agent Card for the MindsDB Agent."""
    capabilities = AgentCapabilities(streaming=True)
    skill = AgentSkill(
        id='chat_with_your_data',
        name='Chat with your data',
        description='Interact with your databases and tables through natural language queries using MindsDB.',
        tags=['database', 'sql', 'mindsdb', 'data analysis'],
        examples=[
            'What TABLES are in my database?',
            'What are some good queries to run on my data?',
        ],
    )
    return AgentCard(
        name='MindsDB Data Chat Agent',
        description="An agent that allows you to interact with your data through natural language queries using MindsDB's capabilities. Query and analyze your databases conversationally.",
        url=f'http://{host}:{port}/',
        version='1.0.0',
        defaultInputModes=MindsDBAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=MindsDBAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill],
    )


if __name__ == '__main__':
    main()
