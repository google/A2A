import os
import random
import traceback

from uuid import uuid4

from agents.google_adk.task_manager import AgentWithTaskManager
from common.client import A2AClient
from common.types import A2AClientError
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import ToolContext


magic_8ball_answers = {
    'affirmative': [
        'It is certain',
        'It is decidedly so',
        'Without a doubt',
        'Yes - definitely',
        'You may rely on it',
        'As I see it, yes',
        'Most likely',
        'Outlook good',
        'Yes',
        'Signs point to yes',
    ],
    'negative': ["Don't count on it", 'My reply is no', 'My sources say no', 'Outlook not so good', 'Very doubtful'],
    'neutral': [
        'Reply hazy, try again',
        'Ask again later',
        'Better not tell you now',
        'Cannot predict now',
        'Concentrate and ask again',
    ],
}


def magic_8ball(question: str, tool_context: ToolContext) -> str:
    """Answers a question as if you were a Magic 8-Ball."""
    if not question.strip():
        return 'Please ask a valid question.'

    # Randomly choose a sentiment
    sentiment = random.choice(list(magic_8ball_answers.keys()))

    # Randomly choose an answer from that sentiment
    return random.choice(magic_8ball_answers[sentiment])


async def proxy_magic_8ball(question: str, tool_context: ToolContext) -> str:
    # Turn off summarization
    tool_context.actions.skip_summarization = True
    # tool_context.actions.escalate = True

    a2a_client = A2AClient(url=os.environ['MAGIC_8BALL_URL'])

    # This should be user-scoped, and secured in a real-world environment but this will suffice for a demonstration
    credentials = tool_context.state.get('user:credentials')
    oauth_redirect_uri = tool_context.state.get('oauth_redirect_uri')

    # Default to what's in the ToolContext, but fall back to the application-specific endpoint
    if not oauth_redirect_uri:
        oauth_redirect_uri = f'{os.environ["PERSONAL_ASSISTANT_URL"]}/auth'

    try:
        payload = {
            'id': str(uuid4()),
            'message': {
                'role': 'user',
                'parts': [
                    {
                        'type': 'text',
                        'text': question,
                    }
                ],
                'messageId': str(uuid4()),
            },
            'configuration': {
                'acceptedOutputModes': ['text'],
            },
        }

        if oauth_redirect_uri:
            payload['message']['metadata'] = {
                'oauth_redirect_uri': oauth_redirect_uri,
            }

        if credentials:
            a2a_client.default_headers = {
                'Authorization': f'Bearer {credentials["token"]}',
            }

        result = await a2a_client.send_message(payload)

        if result.error:
            print(f'\nError sending message {result.model_dump_json(exclude_none=True)}')

        # It would be cool if we could just reutrn an A2A message here...
        return result.result.artifacts[0].parts[0].text
    except Exception as e:
        if isinstance(e, A2AClientError):
            return {
                'data': e.data,
                'message': e.message,
                'status_code': e.status_code,
            }

        traceback.print_exc()

        return {
            'status': 'error',
            'message': f'A2AClient.send_message() failed: {e}',
        }


class PersonalAssistantAgent(AgentWithTaskManager):
    """An agent that behaves as a personal assistant, answering all user questions."""

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']

    def __init__(self):
        super().__init__()
        self._agent = self._build_agent()
        self._user_id = 'remote_agent'
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            session_service=InMemorySessionService(),
        )

    def get_processing_message(self) -> str:
        return 'Processing the Personal Assistant Agent request...'

    def _build_agent(self) -> LlmAgent:
        """Builds the LLM agent for the Personal Assistant Agent."""
        return LlmAgent(
            model='gemini-2.0-flash-001',
            name='personal_assistant_agent',
            description='This agent behaves as a personal assistant and is capable of answering all user questions.',
            instruction="""
You are a helpful AI assistant, behaving as a personal assistant. Answer all user questions accurately and informatively based on your general knowledge.

If a user asks a question that is intended to simulate a Magic 8-Ball, or mimic a Magic 8-Ball, or asks you to consult the Magic 8-Ball, you must use the proxy_magic_8ball tool to generate the response.

Do not answer these questions directly — always defer to the tool for this type of input.

For all other types of questions, answer normally.
""",
            tools=[
                proxy_magic_8ball,
            ],
        )


class Magic8BallAgent(AgentWithTaskManager):
    """An agent that answers user questions as if it were a Magic 8-Ball."""

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']

    def __init__(self):
        super().__init__()
        self._agent = self._build_agent()
        self._user_id = 'remote_agent'
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            session_service=InMemorySessionService(),
        )

    def get_processing_message(self) -> str:
        return 'Processing the Magic 8-Ball request...'

    def _build_agent(self) -> LlmAgent:
        """Builds the LLM agent for the Magic 8-ball agent."""
        return LlmAgent(
            model='gemini-2.0-flash-001',
            name='magic_8ball_agent',
            description='This agent behaves as a Magic 8-Ball.',
            instruction='You are an agent that will answer questions as if you were a Magic 8-Ball.',
            tools=[
                magic_8ball,
            ],
        )
