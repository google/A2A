import asyncio
from uuid import uuid4

from a2a_client.prompt_templates import agent_context_template
from a2a_client.types import AgentContext, Payload, Shared
from pocketflow import AsyncNode

from pocketflow_a2a.a2a_common.client import A2AClient
from pocketflow_a2a.a2a_common.types import AgentCard, SendTaskResponse

from loguru import logger
import colorama


def construct_payload(task_id: str, session_id: str, question: str):
    payload = {
        "id": task_id,
        "sessionId": session_id,
        "message": {
            "role": "user",
            "parts": [
                {
                    "type": "text",  # Explicitly match TextPart structure
                    "text": question,
                }
            ],
        },
        "acceptedOutputModes": ["text", "text/plain"],  # What the client wants back
    }
    return payload


class ExecuteAgentNode(AsyncNode):
    async def prep_async(self, shared: Shared) -> list[tuple[Payload, AgentCard]]:
        logger.info("→ Enter ExecuteAgentNode")
        selected_agents = shared["selected_agents"]
        agents_list = shared["agents_list"]
        session_id = uuid4().hex
        payloads_and_agents = [
            (
                construct_payload(
                    uuid4().hex, session_id, selected_agent["question_to_answer"]
                ),
                agents_list[selected_agent["selected_agent"] - 1],
            )
            for selected_agent in selected_agents
        ]
        shared["payloads_and_agents"] = payloads_and_agents
        return payloads_and_agents

    async def exec_async(
        self, payloads_and_agents: list[tuple[Payload, AgentCard]]
    ) -> list[tuple[tuple[Payload, AgentCard], SendTaskResponse]]:
        logger.info(f"⏳ {colorama.Fore.YELLOW}Executing agents{colorama.Style.RESET_ALL}")
        responses = await asyncio.gather(
            *[
                A2AClient(agent_card=agent_card).send_task(payload, timeout=60)
                for payload, agent_card in payloads_and_agents
            ]
        )
        logger.info(f"✅ {colorama.Fore.GREEN}Finished executing agents{colorama.Style.RESET_ALL}")
        logger.info(f"{colorama.Fore.GREEN}Responses{colorama.Style.RESET_ALL}: {responses}")
        return list(zip(payloads_and_agents, responses))

    async def exec_fallback_async(self, prep_res, exc):
        raise exc

    async def post_async(
        self,
        shared,
        prep_res: list[tuple[Payload, AgentCard]],
        exec_res: list[tuple[tuple[Payload, AgentCard], SendTaskResponse]],
    ):
        agent_contexts = []
        for (payload, agent_card), response in exec_res:
            if response.error:
                continue
            else:
                agent_contexts.append(AgentContext(
                    agent_name=agent_card.name,
                    agent_skills=[skill.model_dump() for skill in agent_card.skills],
                    question=payload["message"]["parts"][0]["text"],
                    answer=response.result.artifacts[-1].parts[0].text
                ))
                shared["artifacts"] = response.result.artifacts
        shared["agent_contexts"] = agent_contexts
        if agent_contexts:
            logger.info("💥 Agent contexts - action")
            shared["agent_contexts_prompt"] = agent_context_template.render(
                agent_contexts=agent_contexts
            )
            return "action"
        else:
            logger.info("👀 No agent contexts - answer with no context")
            shared["agent_contexts_prompt"] = None
            return "answer_with_no_context"
