from typing import Literal, TypedDict

from pocketflow_a2a.a2a_common.client import A2AClient
from pocketflow_a2a.a2a_common.types import AgentCard, Artifact


class SelectedAgent(TypedDict):
    selected_agent: int
    question_to_answer: str


class AgentSkill(TypedDict):
    id: str
    name: str
    description: str
    tags: list[str]
    examples: list[str]
    inputModes: list[str]
    outputModes: list[str]


class AgentContext(TypedDict):
    agent_name: str
    agent_skills: list[AgentSkill]
    question: str
    answer: str


class AnswerMetadata(TypedDict):
    is_information_enough_to_answer: bool
    reason: str


class Answer(TypedDict):
    metadata: AnswerMetadata
    answer: str


class Shared(TypedDict):
    a2a_clients: list[A2AClient]
    agents_list: list[AgentCard]
    available_agents_prompt: str
    selected_agents: list[SelectedAgent]
    agent_contexts: list[AgentContext]
    agent_contexts_prompt: str
    artifacts: list[Artifact]
    answer: Answer
    answer_metadata: AnswerMetadata


class TextPart(TypedDict):
    type: Literal['user', 'assistant', 'system']
    text: str


class Message(TypedDict):
    role: str
    parts: list[TextPart]


class Payload(TypedDict):
    id: str
    sessionId: str
    message: Message
    acceptedOutputModes: list[str]


class AgentContext(TypedDict):
    agent_name: str
    agent_skills: list[str]
    question: str
    answer: str
