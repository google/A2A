"""This file serves as the main entry point for the Shibuya Cafe Agent.

It initializes the A2A server, defines the agent's capabilities,
and starts the server to handle incoming requests.
"""

import logging
import os

import click

from agent import ShibuyaCafeAgent
from common.server import A2AServer
from common.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    MissingAPIKeyError,
)
from dotenv import load_dotenv
from task_manager import AgentTaskManager


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option('--host', 'host', default='localhost')
@click.option('--port', 'port', default=10003)
def main(host, port):
    """Entry point for the A2A Shibuya Cafe Agent."""
    try:
        if not os.getenv('GOOGLE_API_KEY'):
            raise MissingAPIKeyError('GOOGLE_API_KEY environment variable not set.')

        capabilities = AgentCapabilities(streaming=False)
        skill = AgentSkill(
            id='shibuya_cafe',
            name='Shibuya Cafe Guide',
            description='渋谷のカフェに関する情報やおすすめを提供します。',
            tags=['cafe', 'shibuya', 'recommendation', 'カフェ', '渋谷'],
            examples=['渋谷でおすすめのカフェを教えて', '電源が使える渋谷のカフェは？'],
        )

        agent_card = AgentCard(
            name='Shibuya Cafe Agent',
            description='渋谷のカフェに関する情報やおすすめを提供するエージェントです。',
            url=f'http://{host}:{port}/',
            version='1.0.0',
            defaultInputModes=ShibuyaCafeAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=ShibuyaCafeAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=ShibuyaCafeAgent()),
            host=host,
            port=port,
        )
        logger.info(f'Starting ShibuyaCafeAgent server on {host}:{port}')
        server.start()
    except MissingAPIKeyError as e:
        logger.error(f'Error: {e}')
        exit(1)
    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        exit(1)


if __name__ == '__main__':
    main()
