"""A an example of serving a resilient agent using restate.dev"""

import os
from fastapi import FastAPI
import restate
from agent import ReimbursementAgent
from middleware import AgentMiddleware
from dotenv import load_dotenv

from common.types import AgentCapabilities, AgentCard, AgentSkill, MissingAPIKeyError

load_dotenv()

RESTATE_HOST = os.getenv("RESTATE_HOST", "http://localhost:8080")

AGENT_CARD = AgentCard(
    name="ReimbursementAgent",
    description="This agent handles the reimbursement process for the employees given the amount and purpose of the reimbursement.",
    url=RESTATE_HOST,
    version="1.0.0",
    defaultInputModes=ReimbursementAgent.SUPPORTED_CONTENT_TYPES,
    defaultOutputModes=ReimbursementAgent.SUPPORTED_CONTENT_TYPES,
    capabilities=AgentCapabilities(streaming=False),
    skills=[
        AgentSkill(id="process_reimbursement",
                   name="Process Reimbursement Tool",
                   description="Helps with the reimbursement process for users given the amount and purpose of the reimbursement.",
                   tags=["reimbursement"],
                   examples=["Can you reimburse me $20 for my lunch with the clients?"])],
)

REIMBURSEMENT_AGENT = AgentMiddleware(AGENT_CARD, ReimbursementAgent())

app = FastAPI()

@app.get("/.well-known/agent.json")
async def agent_json():
    """serve the agent card"""
    return REIMBURSEMENT_AGENT.agent_card_json

app.mount("/restate/v1", restate.app(REIMBURSEMENT_AGENT))

def main():
    """Serve the agent at a specified port using hypercorn."""
    import asyncio
    import hypercorn
    import hypercorn.asyncio

    if not os.getenv('GOOGLE_API_KEY'):
        raise MissingAPIKeyError(
            'GOOGLE_API_KEY environment variable not set.'
        )

    port = os.getenv("AGENT_PORT", "9080")
    conf = hypercorn.Config()
    conf.bind = [f"0.0.0.0:{port}"]
    asyncio.run(hypercorn.asyncio.serve(app, conf))

if __name__ == "__main__":
    main()
