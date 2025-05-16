import logging
import os

logging.basicConfig(
    level=os.environ.get("LOGLEVEL", "DEBUG").upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

import click
from agent import VideoGenerationAgent
from common.server import A2AServer
from common.types import (AgentCapabilities, AgentCard, AgentSkill,
                          MissingAPIKeyError)
from dotenv import load_dotenv
from task_manager import AgentTaskManager

load_dotenv()

logger = logging.getLogger(__name__)


@click.command()
@click.option('--host', default='localhost')
@click.option('--port', default=10002)
def main(host, port):
    logger.info(f"Application starting. Effective logging level for root: {logging.getLevelName(logging.getLogger().getEffectiveLevel())}")
    try:
        # Check for API key only if Vertex AI is not configured
        if not os.getenv('GOOGLE_GENAI_USE_VERTEXAI') == 'TRUE':
            if not os.getenv('GOOGLE_API_KEY'):
                raise MissingAPIKeyError(
                    'GOOGLE_API_KEY environment variable not set and GOOGLE_GENAI_USE_VERTEXAI is not TRUE.'
                )

        capabilities = AgentCapabilities(streaming=True)
        skill = AgentSkill(
            id='generate_video_from_prompt',
            name='Generate Video from Text Prompt',
            description='Generates a video based on a textual description and returns a GCS URL to the video.',
            tags=['video', 'generation', 'multimedia'],
            examples=[
                'Create a short video of a cat playing with a yarn ball.',
                'Generate a video showing a sunset over a mountain range.'
            ],
        )
        agent_card = AgentCard(
            name='Video Generation Agent (Simulated)',
            description='This agent simulates generating a video from a text prompt and provides periodic updates.',
            url=f'http://{host}:{port}/',
            version='1.0.0',
            defaultInputModes=VideoGenerationAgent.SUPPORTED_CONTENT_TYPES, 
            defaultOutputModes=['text', 'text/plain', 'text/uri-list', 'video/mp4'], # Added video/mp4 to indicate video output
            capabilities=capabilities,
            skills=[skill],
        )
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=VideoGenerationAgent()),
            host=host,
            port=port,
        )
        server.start()
    except MissingAPIKeyError as e:
        logger.error(f'Error: {e}')
        exit(1)
    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        exit(1)


if __name__ == '__main__':
    main()
