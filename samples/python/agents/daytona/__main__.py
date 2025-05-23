from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from agents.daytona.task_manager import AgentTaskManager
from agents.daytona.agent import DaytonaSandboxAgent
import click
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=10004)
def main(host, port):
    try:
        capabilities = AgentCapabilities(streaming=True)

        create_skill = AgentSkill(
            id="create_sandbox",
            name="Create Sandbox",
            description="Creates a new sandbox for running code with specified configuration.",
            tags=["sandbox", "create", "code"],
            examples=[
                "Create a Python sandbox with 2 CPU cores and 4GB of memory",
                "Set up a JavaScript sandbox for running web code"
            ],
        )

        execute_skill = AgentSkill(
            id="execute_code",
            name="Execute Code",
            description="Runs code or commands in a sandbox environment.",
            tags=["sandbox", "execute", "code", "command"],
            examples=[
                "Run this Python script in a sandbox",
                "Execute 'npm install' in my sandbox"
            ],
        )

        manage_skill = AgentSkill(
            id="manage_sandbox",
            name="Manage Sandbox",
            description="Start, stop, or destroy sandboxes.",
            tags=["sandbox", "manage", "start", "stop", "destroy"],
            examples=[
                "Start my sandbox",
                "Stop all running sandboxes",
                "Destroy the sandbox I created earlier"
            ],
        )

        agent_card = AgentCard(
            name="Daytona Sandbox Orchestration Agent",
            description="This agent orchestrates Daytona sandboxes for running code and executing commands in isolated environments.",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=DaytonaSandboxAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=DaytonaSandboxAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[create_skill, execute_skill, manage_skill],
        )

        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=DaytonaSandboxAgent()),
            host=host,
            port=port,
        )
        server.start()
    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)

if __name__ == "__main__":
    main()