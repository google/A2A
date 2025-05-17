import json
import re

from a2a_client.prompt_templates import action_template
from a2a_client.types import Shared
from a2a_client.utils import call_llm
from pocketflow import AsyncNode
from loguru import logger


class ActionNode(AsyncNode):
    @staticmethod
    def extract_metadata_and_answer(text):
        # Extract JSON metadata block
        metadata_match = re.search(
            r"# metadata\s*```json\s*({.*?})\s*```", text, re.DOTALL
        )
        metadata = None
        if metadata_match:
            metadata_str = metadata_match.group(1)
            metadata = json.loads(metadata_str)

        # Extract answer block
        answer_match = re.search(r"# answer\s*(.*?)={5,}", text, re.DOTALL)
        answer = None
        if answer_match:
            answer = answer_match.group(1).strip()

        return metadata, answer

    async def prep_async(self, shared: Shared) -> str:
        logger.info("💥 Enter ActionNode")
        action_prompt = action_template.render(
            question=shared["question"], context=shared["agent_contexts_prompt"]
        )
        return action_prompt

    async def exec_async(self, action_prompt: str) -> str:
        return call_llm(action_prompt)

    async def post_async(self, shared: Shared, prep_res: str, exec_res: str) -> str:
        metadata, answer = self.extract_metadata_and_answer(exec_res)
        shared["answer"] = answer
        shared["answer_metadata"] = metadata
        is_information_enough_to_answer = metadata["is_information_enough_to_answer"]
        if is_information_enough_to_answer:
            logger.info("🚀 Answer is enough to answer the question")
            return "done"
        else:
            logger.info("📝 Answer is not enough to answer the question")
            return "select_agent"
