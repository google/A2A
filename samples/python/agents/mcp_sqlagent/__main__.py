from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from common.utils.push_notification_auth import PushNotificationSenderAuth
from task_manager import AgentTaskManager
from agent import MCPAgent
import click
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10020)
def main(host, port):
    """Starts the MCP Agent server."""
    try:
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise MissingAPIKeyError("ANTHROPIC_API_KEY environment variable not set.")

        capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
        skill = AgentSkill(
            id="sql_assistant",
            name="SQL Assistant",
            description="Helps with SQL database operations and queries",
            tags=["sqlite", "database", "sql"],
            examples=["Show me all tables in the database", "Execute this SQL query"],
        )
        agent_card = AgentCard(
            name="MCP SQL Agent",
            description="An AI assistant that helps with SQL database operations",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=MCPAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=MCPAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        notification_sender_auth = PushNotificationSenderAuth()
        notification_sender_auth.generate_jwk()
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=MCPAgent(), notification_sender_auth=notification_sender_auth),
            host=host,
            port=port,
        )

        server.app.add_route(
            "/.well-known/jwks.json", notification_sender_auth.handle_jwks_endpoint, methods=["GET"]
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