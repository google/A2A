"""
This is a sample agent that uses the Marvin framework to extract structured contact information from text.
It is integrated with the Agent2Agent (A2A) protocol.
"""

import logging

import click
import httpx

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, InMemoryPushNotifier
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from agents.marvin.agent import ExtractorAgent
from common.server import A2AServer
from common.types import AgentCapabilities, AgentCard, AgentSkill
from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr, Field

from agent import ExtractorAgent  # type: ignore[import-untyped]
from agent_executor import ExtractorAgentExecutor  # type: ignore[import-untyped]

load_dotenv()

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
    agent = ExtractorAgent(instructions=instructions, result_type=result_type)
    httpx_client = httpx.AsyncClient()
    request_handler = DefaultRequestHandler(
        agent_executor=ExtractorAgentExecutor(agent=agent),
        task_store=InMemoryTaskStore(),
        push_notifier=InMemoryPushNotifier(httpx_client),
    )
    server = A2AStarletteApplication(
        agent_card=get_agent_card(host, port), http_handler=request_handler
    )
    import uvicorn

    uvicorn.run(server.build(), host=host, port=port)


def get_agent_card(host: str, port: int):
    """Returns the Agent Card for the ExtractorAgent."""
    capabilities = AgentCapabilities(streaming=True)
    skill = AgentSkill(
        id="extract_contacts",
        name="Contact Information Extraction",
        description="Extracts structured contact information from text",
        tags=["contact info", "structured extraction", "information extraction"],
        examples=[
            "My name is John Doe, email: john@example.com, phone: (555) 123-4567"
        ],
    )
    return AgentCard(
        name="Marvin Contact Extractor",
        description="Extracts structured contact information from text using Marvin's extraction capabilities",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=ExtractorAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=ExtractorAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill],
    )


if __name__ == "__main__":
    main()
