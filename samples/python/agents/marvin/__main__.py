"""
This is a sample agent that uses the Marvin framework to extract structured contact information from text.
It is integrated with the Agent2Agent (A2A) protocol.
"""

import logging

import click
from agents.marvin.agent import ExtractorAgent
from agents.marvin.task_manager import AgentTaskManager
from common.server import A2AServer
from common.types import AgentCapabilities, AgentCard, AgentSkill
from common.utils.push_notification_auth import PushNotificationSenderAuth
from pydantic import BaseModel, EmailStr, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContactInfo(BaseModel):
    """Structured contact information extracted from text."""

    name: str = Field(description="Person's first and last name")
    email: EmailStr = Field(description="Email address")
    phone: str = Field(description="Phone number if present")
    organization: str | None = Field(
        None, description="Organization or company if mentioned"
    )
    role: str | None = Field(None, description="Job title or role if mentioned")


@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10030)
@click.option("--result-type", "result_type", default="ContactInfo")
@click.option(
    "--instructions",
    "instructions",
    default="Politely interrogate the user for their contact information. The schema of the result type implies what things you _need_ to get from the user.",
)
def main(host, port, result_type, instructions):
    """Starts the Marvin Contact Extractor Agent server."""
    try:
        result_type = eval(result_type)
    except Exception as e:
        logger.error(f"Invalid result type: {e}")
        exit(1)

    try:
        capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
        skill = AgentSkill(
            id="extract_contacts",
            name="Contact Information Extraction",
            description="Extracts structured contact information from text",
            tags=["contact info", "structured extraction", "information extraction"],
            examples=[
                "My name is John Doe, email: john@example.com, phone: (555) 123-4567"
            ],
        )
        agent_card = AgentCard(
            name="Marvin Contact Extractor",
            description="Extracts structured contact information from text using Marvin's extraction capabilities",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=ExtractorAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=ExtractorAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        notification_sender_auth = PushNotificationSenderAuth()
        notification_sender_auth.generate_jwk()
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(
                agent=ExtractorAgent(
                    instructions=instructions, result_type=result_type
                ),
                notification_sender_auth=notification_sender_auth,
            ),
            host=host,
            port=port,
        )

        server.app.add_route(
            "/.well-known/jwks.json",
            notification_sender_auth.handle_jwks_endpoint,
            methods=["GET"],
        )

        logger.info(f"Starting Marvin Contact Extractor server on {host}:{port}")
        server.start()
    except Exception as e:
        logger.exception(f"An error occurred during server startup: {e}", exc_info=e)
        exit(1)


if __name__ == "__main__":
    main()
