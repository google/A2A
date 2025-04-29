from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from common.utils.push_notification_auth import PushNotificationSenderAuth
from agents.llama_index_file_chat.task_manager import LlamaIndexTaskManager
from agents.llama_index_file_chat.agent import ParseAndChat
import click
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10010)
def main(host, port):
    """Starts the Currency Agent server."""
    try:
        if not os.getenv("GOOGLE_API_KEY"):
            raise MissingAPIKeyError("GOOGLE_API_KEY environment variable not set.")
        if not os.getenv("LLAMA_CLOUD_API_KEY"):
            raise MissingAPIKeyError("LLAMA_CLOUD_API_KEY environment variable not set.")

        capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
        
        skill = AgentSkill(
            id="parse_and_chat",
            name="Parse and Chat",
            description="Parses a file and then chats with a user using the parsed content as context.",
            tags=["parse", "chat", "file", "llama_parse"],
            examples=["What does this file talk about?"],
        )

        agent_card = AgentCard(
            name="Parse and Chat",
            description="Parses a file and then chats with a user using the parsed content as context.",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=LlamaIndexTaskManager.SUPPORTED_INPUT_TYPES,
            defaultOutputModes=LlamaIndexTaskManager.SUPPORTED_OUTPUT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        notification_sender_auth = PushNotificationSenderAuth()
        notification_sender_auth.generate_jwk()
        server = A2AServer(
            agent_card=agent_card,
            task_manager=LlamaIndexTaskManager(
                agent=ParseAndChat(), 
                notification_sender_auth=notification_sender_auth
            ),
            host=host,
            port=port,
        )

        server.app.add_route(
            "/.well-known/jwks.json", 
            notification_sender_auth.handle_jwks_endpoint,
            methods=["GET"]
        )

        logger.info(f"Starting server on {host}:{port}")
        server.start()
    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)


if __name__ == "__main__":
    main()
