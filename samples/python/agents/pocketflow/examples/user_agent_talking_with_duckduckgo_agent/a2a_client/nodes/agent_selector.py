import json
import re
from typing import cast

from a2a_client.prompt_templates import agent_selector_template
from a2a_client.types import SelectedAgent
from a2a_client.utils import call_llm
from pocketflow import AsyncNode
from loguru import logger


def parse_json_string(s: str) -> dict:
    """
    Parse a string containing JSON (optionally wrapped in markdown code block) into a Python dictionary.
    """
    # Remove leading/trailing whitespace
    s = s.strip()
    # Remove markdown code block if present
    # Handles ```json ... ``` or ``` ... ```
    code_block_pattern = r"^```(?:json)?\s*([\s\S]*?)\s*```$"
    match = re.match(code_block_pattern, s, re.IGNORECASE)
    if match:
        s = match.group(1).strip()
    # Now parse as JSON
    return json.loads(s)


class AgentSelectorNode(AsyncNode):
    async def prep_async(self, shared):
        logger.info("👀 Enter AgentSelectorNode")
        return (shared["question"], shared["available_agents_prompt"])

    async def exec_async(self, inputs):
        question, available_agents_prompt = inputs
        prompt = agent_selector_template.render(
            question=question, available_agents_prompt=available_agents_prompt
        )
        return call_llm(prompt)

    async def post_async(self, shared, prep_res, exec_res):
        shared["selected_agents"] = cast(
            list[SelectedAgent], parse_json_string(exec_res)
        )
        if shared["selected_agents"]:
            logger.info("💬 Selected agents - execute agent calling")
            return "execute_agent"
        else:
            logger.info("🔍 No selected agents - answer with no context")
            return "answer_with_no_context"
