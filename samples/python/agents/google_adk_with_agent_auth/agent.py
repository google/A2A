import random
from agents.google_adk.task_manager import AgentWithTaskManager
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService


magic_8ball_answers = {
    "affirmative": [
        "It is certain",
        "It is decidedly so",
        "Without a doubt",
        "Yes - definitely",
        "You may rely on it",
        "As I see it, yes",
        "Most likely",
        "Outlook good",
        "Yes",
        "Signs point to yes"
    ],
    "negative": [
        "Don't count on it",
        "My reply is no",
        "My sources say no",
        "Outlook not so good",
        "Very doubtful"
    ],
    "neutral": [
        "Reply hazy, try again",
        "Ask again later",
        "Better not tell you now",
        "Cannot predict now",
        "Concentrate and ask again"
    ]
}



def magic_8ball(question: str) -> str:
    '''Answers a question as if you were a Magic 8-Ball.'''
    if not question.strip():
        return "Please ask a valid question."

    # Randomly choose a sentiment
    sentiment = random.choice(list(magic_8ball_answers.keys()))

    # Randomly choose an answer from that sentiment
    answer = random.choice(magic_8ball_answers[sentiment])

    return answer


class Magic8BallAgent(AgentWithTaskManager):
    '''An agent that answers user questions as if it were a Magic 8-Ball.'''

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']

    def __init__(self):
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
        '''Builds the LLM agent for the Magic 8-ball agent.'''
        return LlmAgent(
            model='gemini-2.0-flash-001',
            name='magic_8ball_agent',
            description='This agent answers user questions as if you were a Magic 8-Ball.',
            instruction='You are an agent that will answer user questions as if you were a Magic 8-Ball.',
            tools=[
                magic_8ball,
            ],
    )
