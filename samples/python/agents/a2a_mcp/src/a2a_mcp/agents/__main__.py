# type: ignore

import json
import logging

import click
from activity_planner_agent import ActivityPlannerAgent
from adk_travel_agent import TravelAgent
from common.server import A2AServer
from common.types import AgentCard, MissingAPIKeyError
from common.utils.push_notification_auth import PushNotificationSenderAuth
from langgraph_planner_agent import LangraphPlannerAgent
from task_executor_agent import TaskExecutorAgent

from a2a_mcp.common import prompts
from a2a_mcp.common.task_manager import AgentTaskManager
from a2a_mcp.common.utils import config_logger

logger = logging.getLogger(__name__)
config_logger(logger=logger)


def get_agent(agent_card: AgentCard):
    try:
        if agent_card.name == "Activity Planner Agent":
            return ActivityPlannerAgent()
        elif agent_card.name == "Orchestrator Agent":
            return TaskExecutorAgent()
        elif agent_card.name == "Langraph Planner Agent":
            return LangraphPlannerAgent()
        elif agent_card.name == "Air Ticketing Agent":
            return TravelAgent(
                agent_name="AirTicketingAgent",
                description="Book air tickets given a criteria",
                instructions=prompts.AIR_TRAVEL_INSTRUCTIONS,
            )
        elif agent_card.name == "Hotel Booking Agent":
            return TravelAgent(
                agent_name="HotelBookingAgent",
                description="Book hotels given a criteria",
                instructions=prompts.HOTEL_BOOKING_INSTRUCTIONS,
            )
        elif agent_card.name == "Car Rental Agent":
            return TravelAgent(
                agent_name="CarRentalBookingAgent",
                description="Book rental cars given a criteria",
                instructions=prompts.RENTAL_CAR_BOOKING_INSTRUCTIONS,
            )
            # return LangraphCarRentalAgent()
    except Exception as e:
        raise e


@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10101)
@click.option("--agent-card", "agent_card")
def main(host, port, agent_card):
    """Starts an Agent server."""
    try:
        if not agent_card:
            raise ValueError("Agent card is required")
        with open(agent_card, "r") as file:
            data = json.load(file)
        agent_card = AgentCard(**data)

        notification_sender_auth = PushNotificationSenderAuth()
        notification_sender_auth.generate_jwk()
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(
                agent=get_agent(agent_card),
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

        logger.info(f"Starting server on {host}:{port}")
        server.start()
    except FileNotFoundError:
        logger.error(f"Error: File '{agent_card}' not found.")
        exit(1)
    except json.JSONDecodeError:
        logger.error(f"Error: File '{agent_card}' contains invalid JSON.")
        exit(1)
    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)


if __name__ == "__main__":
    main()
