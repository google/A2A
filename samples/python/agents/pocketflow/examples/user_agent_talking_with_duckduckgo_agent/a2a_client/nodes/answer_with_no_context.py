from loguru import logger
from pocketflow import AsyncNode

from a2a_client.prompt_templates import answer_question_with_no_context_template
from a2a_client.types import Shared
from a2a_client.utils import call_llm


class AnswerWithNoContextNode(AsyncNode):
    async def prep_async(self, shared: Shared) -> str:
        logger.info('🔍 Answer with no context')
        prompt = answer_question_with_no_context_template.render(
            question=shared['question'],
        )
        return prompt

    async def exec_async(self, prompt: str) -> str:
        return call_llm(prompt)

    async def post_async(
        self, shared: Shared, prep_res: str, exec_res: str
    ) -> str:
        logger.info(f'💬 Answer: {exec_res}')
        shared['answer'] = exec_res
        return 'done'
