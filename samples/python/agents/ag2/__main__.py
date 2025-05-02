from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from agents.ag2.task_manager import AgentTaskManager
from agents.ag2.agent import YoutubeMCPAgent
import click
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10003)
def main(host, port):
    """Starts the AG2 MCP Agent server."""
    try:
        if not os.getenv("OPENAI_API_KEY"):
            raise MissingAPIKeyError("OPENAI_API_KEY environment variable not set.")

        capabilities = AgentCapabilities(streaming=True)
        skills = [
            AgentSkill(
                id="download_closed_captions",
                name="Download YouTube Closed Captions",
                description="Retrieve closed captions/transcripts from YouTube videos",
                tags=["youtube", "captions", "transcription", "video"],
                examples=[
                    "Extract the transcript from this YouTube video: https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    "Download the captions for this YouTube tutorial"
                ]
            )
        ]

        agent_card = AgentCard(
            name="YouTube Captions Agent",
            description="AI agent that can extract closed captions and transcripts from YouTube videos. This agent provides raw transcription data that can be used for further processing.",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=YoutubeMCPAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=YoutubeMCPAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=skills,
        )

        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=YoutubeMCPAgent()),
            host=host,
            port=port,
        )

        logger.info(f"Starting AG2 Youtube MCP agent on {host}:{port}")
        server.start()
    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)


if __name__ == "__main__":
    main()
