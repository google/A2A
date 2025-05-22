import logging
import os

import click
import httpx

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, InMemoryPushNotifier
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from agent_executor import LlamaIndexAgentExecutor
from agents.llama_index_file_chat.agent import ParseAndChat
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""

    pass


@click.command()
@click.option('--host', 'host', default='localhost')
@click.option('--port', 'port', default=10010)
def main(host, port):
    """Starts the Currency Agent server."""
    try:
        if not os.getenv('GOOGLE_API_KEY'):
            raise MissingAPIKeyError(
                'GOOGLE_API_KEY environment variable not set.'
            )
        if not os.getenv('LLAMA_CLOUD_API_KEY'):
            raise MissingAPIKeyError(
                'LLAMA_CLOUD_API_KEY environment variable not set.'
            )

        capabilities = AgentCapabilities(streaming=True, pushNotifications=True)

        skill = AgentSkill(
            id='parse_and_chat',
            name='Parse and Chat',
            description='Parses a file and then chats with a user using the parsed content as context.',
            tags=['parse', 'chat', 'file', 'llama_parse'],
            examples=['What does this file talk about?'],
        )

        agent_card = AgentCard(
            name='Parse and Chat',
            description='Parses a file and then chats with a user using the parsed content as context.',
            url=f'http://{host}:{port}/',
            version='1.0.0',
            defaultInputModes=LlamaIndexAgentExecutor.SUPPORTED_INPUT_TYPES,
            defaultOutputModes=LlamaIndexAgentExecutor.SUPPORTED_OUTPUT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        httpx_client = httpx.AsyncClient()
        request_handler = DefaultRequestHandler(
            agent_executor=LlamaIndexAgentExecutor(
                agent=ParseAndChat(),
            ),
            task_store=InMemoryTaskStore(),
            push_notifier=InMemoryPushNotifier(httpx_client),
        )
        server = A2AStarletteApplication(
            agent_card=agent_card, http_handler=request_handler
        )
        import uvicorn

        uvicorn.run(server.build(), host=host, port=port)
    except MissingAPIKeyError as e:
        logger.error(f'Error: {e}')
        exit(1)
    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        exit(1)


if __name__ == '__main__':
    main()
