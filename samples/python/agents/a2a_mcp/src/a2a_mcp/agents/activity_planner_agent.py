# type: ignore

import json
import logging

from google.adk.agents import Agent
from google.genai import types as genai_types

from a2a_mcp.common import prompts
from a2a_mcp.common.agent_runner import AgentRunner
from a2a_mcp.common.base_agent import BaseAgent
from a2a_mcp.common.types import AgentResponse, TaskList
from a2a_mcp.common.utils import config_logger, init_api_key

logger = logging.getLogger(__name__)


class ActivityPlannerAgent(BaseAgent):
    def __init__(self):
        init_api_key()
        config_logger(logger=logger)

        logger.info("Initializing TaskPlannerAgent")

        super().__init__(
            agent_name="TaskPlannerAgent",
            description="Breakdown the user request into executable tasks",
            content_types=["text", "text/plain"],
        )
        generate_content_config = genai_types.GenerateContentConfig(temperature=0.0)
        self.agent = Agent(
            name=self.agent_name,
            instruction=prompts.PLANNER_INSTRUCTIONS,
            output_schema=TaskList,
            model="gemini-2.0-flash",
            disallow_transfer_to_parent=True,
            disallow_transfer_to_peers=True,
            generate_content_config=generate_content_config,
        )
        self.runner = AgentRunner()

    async def generate_plan(self, query: str, session_id: str = None) -> TaskList:
        if not query:
            raise ValueError("Query cannot be empty")

        response = await self.runner.run_agent(self.agent, query, session_id)
        logger.info(f"Generated Plan : {response.content.parts[0].text}")
        return TaskList(**json.loads(response.content.parts[0].text))

    async def invoke(self, query, session_id) -> dict:
        logger.info(f"Running TaskPlannerAgent for session {session_id}")
        task_list = await self.generate_plan(query)
        return {"TaskList", task_list}

    async def get_agent_response() -> AgentResponse:
        pass
