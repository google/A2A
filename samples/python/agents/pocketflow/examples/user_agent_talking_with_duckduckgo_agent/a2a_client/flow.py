from .nodes.action import ActionNode
from .nodes.agent_selector import AgentSelectorNode
from .nodes.answer_with_no_context import AnswerWithNoContextNode
from .nodes.done import DoneNode
from .nodes.execute_agent import ExecuteAgentNode
from .nodes.get_available_agents import GetAvailableAgentsNode
from pocketflow import AsyncFlow

from pocketflow_a2a.a2a_common.client import A2AClient


def create_flow():
    get_available_agents_node = GetAvailableAgentsNode()
    agent_selector_node = AgentSelectorNode()
    execute_agent_node = ExecuteAgentNode()
    answer_with_no_context_node = AnswerWithNoContextNode()
    action_node = ActionNode()
    done_node = DoneNode()

    get_available_agents_node - "agent_selector" >> agent_selector_node
    get_available_agents_node - "answer_with_no_context" >> answer_with_no_context_node

    # Select agent
    agent_selector_node - "execute_agent" >> execute_agent_node
    agent_selector_node - "answer_with_no_context" >> answer_with_no_context_node

    # Execute agent
    execute_agent_node - "action" >> action_node
    execute_agent_node - "answer_with_no_context" >> answer_with_no_context_node

    # Action
    action_node - "done" >> done_node
    action_node - "select_agent" >> agent_selector_node

    flow = AsyncFlow(start=get_available_agents_node)

    return flow


if __name__ == "__main__":
    import asyncio

    flow = create_flow()
    shared = {
        "question": "Who won the Nobel Prize in Physics 2024?",
        "a2a_clients": [A2AClient(url="http://localhost:10003")],
    }
    print(asyncio.run(flow.run_async(shared)))
    print(shared["answer"])