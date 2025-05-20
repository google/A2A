import click
import os
import logging

from agents.llama_index_file_chat.agent import ParseAndChat
from agent_executor import LlamaIndexAgentExecutor
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication
from a2a.types import (
    AgentAuthentication,
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from common.utils.push_notification_auth import PushNotificationSenderAuth
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
            authentication=AgentAuthentication(schemes=[]),
        )

        notification_sender_auth = PushNotificationSenderAuth()
        notification_sender_auth.generate_jwk()
        request_handler = DefaultRequestHandler(
            agent_executor=LlamaIndexAgentExecutor(
                agent=ParseAndChat(),
                notification_sender_auth=notification_sender_auth,
            ),
            task_store=InMemoryTaskStore(),
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
