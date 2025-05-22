"""This file serves as the main entry point for the application.

It initializes the A2A server, defines the agent's capabilities,
and starts the server to handle incoming requests.
"""

import logging
import os

import click

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from agent import ImageGenerationAgent
from agent_executor import ImageGenerationAgentExecutor
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""

    pass


@click.command()
@click.option('--host', 'host', default='localhost')
@click.option('--port', 'port', default=10001)
def main(host, port):
    """Entry point for the A2A + CrewAI Image generation sample."""
    try:
        if not os.getenv('GOOGLE_API_KEY') and not os.getenv(
            'GOOGLE_GENAI_USE_VERTEXAI'
        ):
            raise MissingAPIKeyError(
                'GOOGLE_API_KEY or Vertex AI environment variables not set.'
            )

        capabilities = AgentCapabilities(streaming=False)
        skill = AgentSkill(
            id='image_generator',
            name='Image Generator',
            description=(
                'Generate stunning, high-quality images on demand and leverage'
                ' powerful editing capabilities to modify, enhance, or completely'
                ' transform visuals.'
            ),
            tags=['generate image', 'edit image'],
            examples=['Generate a photorealistic image of raspberry lemonade'],
        )

        agent_card = AgentCard(
            name='Image Generator Agent',
            description=(
                'Generate stunning, high-quality images on demand and leverage'
                ' powerful editing capabilities to modify, enhance, or completely'
                ' transform visuals.'
            ),
            url=f'http://{host}:{port}/',
            version='1.0.0',
            defaultInputModes=ImageGenerationAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=ImageGenerationAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        request_handler = DefaultRequestHandler(
            agent_executor=ImageGenerationAgentExecutor(),
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
