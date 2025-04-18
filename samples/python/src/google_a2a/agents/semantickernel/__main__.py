import logging

import click
from common.server import A2AServer
from common.types import AgentCapabilities, AgentCard, AgentSkill
from common.utils.push_notification_auth import PushNotificationSenderAuth
from dotenv import load_dotenv

from agents.semantickernel.task_manager import TaskManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=10020)
def main(host, port):
    """Starts the Semantic Kernel Agent server using A2A."""
    # Build the agent card
    capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
    skill_trip_planning = AgentSkill(
        id="trip_planning_sk",
        name="Semantic Kernel Trip Planning",
        description=(
            "Handles comprehensive trip planning, including currency exchanges, itinerary creation, sightseeing, "
            "dining recommendations, and event bookings using Frankfurter API for currency conversions."
        ),
        tags=["trip", "planning", "travel", "currency", "semantic-kernel"],
        examples=[
            "Plan a budget-friendly day trip to Seoul including currency exchange.", 
            "What's the exchange rate and recommended itinerary for visiting Tokyo?",
        ]
    )

    agent_card = AgentCard(
        name="SK Travel Agent",
        description=(
            "Semantic Kernel-based travel agent providing comprehensive trip planning services "
            "including currency exchange and personalized activity planning."
        ),
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=capabilities,
        skills=[skill_trip_planning],
    )

    # Prepare push notification system
    notification_sender_auth = PushNotificationSenderAuth()
    notification_sender_auth.generate_jwk()

    # Create the server
    task_manager = TaskManager(notification_sender_auth=notification_sender_auth)
    server = A2AServer(agent_card=agent_card, task_manager=task_manager, host=host, port=port)
    server.app.add_route("/.well-known/jwks.json", notification_sender_auth.handle_jwks_endpoint, methods=["GET"])

    logger.info(f"Starting the Semantic Kernel agent server on {host}:{port}")
    server.start()


if __name__ == "__main__":
    main()
