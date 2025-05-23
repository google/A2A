import os

from collections.abc import AsyncIterable
from typing import Any, Literal

import httpx

from auth0.authentication.get_token import GetToken
from auth0.management import Auth0
from auth0_ai_langchain.auth0_ai import Auth0AI
from auth0_ai_langchain.ciba import get_ciba_credentials
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel


auth0_ai = Auth0AI(
    auth0={
        'domain': os.getenv('HR_AUTH0_DOMAIN'),
        'client_id': os.getenv('HR_AGENT_AUTH0_CLIENT_ID'),
        'client_secret': os.getenv('HR_AGENT_AUTH0_CLIENT_SECRET'),
    }
)


with_async_user_confirmation = auth0_ai.with_async_user_confirmation(
    binding_message=(
        'Approve sharing your employment details with an external party.'
    ),
    scopes=['read:employee'],
    user_id=lambda employee_id, **__: employee_id,
    audience=os.getenv('HR_API_AUTH0_AUDIENCE'),
    on_authorization_request='block',  # TODO: this is just for demo purposes
)


get_token = GetToken(
    domain=os.getenv('HR_AUTH0_DOMAIN'),
    client_id=os.getenv('HR_AGENT_AUTH0_CLIENT_ID'),
    client_secret=os.getenv('HR_AGENT_AUTH0_CLIENT_SECRET'),
)


@tool
async def is_active_employee(employee_id: str) -> dict[str, Any]:
    """Confirm whether a person is an active employee of the company.

    Args:
        employee_id (str): The employee's identification.

    Returns:
        dict: A dictionary containing the employment status, or an error message
        if the request fails.
    """
    try:
        credentials = get_ciba_credentials()
        response = await httpx.AsyncClient().get(
            f'{os.getenv("HR_API_BASE_URL", "http://localhost:10051")}/employees/{employee_id}',
            headers={
                'Authorization': (
                    f'{credentials["token_type"]} {credentials["access_token"]}'
                ),
                'Content-Type': 'application/json',
            },
        )

        if response.status_code == 404:
            return {'active': False}
        if response.status_code == 200:
            return {'active': True}
        response.raise_for_status()
    except httpx.HTTPError as e:
        return {'error': f'HR API request failed: {e}'}
    except Exception:
        return {'error': 'Unexpected response from HR API.'}


@tool
def get_employee_id_by_email(work_email: str) -> dict[str, Any] | None:
    """Return the employee ID by email.

    Args:
        work_email (str): The employee's work email.

    Returns:
        dict: A dictionary containing the employee ID if it exists, otherwise
        None.
    """
    try:
        user = Auth0(
            domain=get_token.domain,
            token=get_token.client_credentials(
                f'https://{os.getenv("HR_AUTH0_DOMAIN")}/api/v2/'
            )['access_token'],
        ).users_by_email.search_users_by_email(
            email=work_email, fields=['user_id']
        )[0]

        return {'employee_id': user['user_id']} if user else None
    except Exception:
        return {'error': 'Unexpected response from Auth0 Management API.'}


class ResponseFormat(BaseModel):
    """Respond to the user in this format."""

    status: Literal['completed', 'input-required', 'failed'] = 'failed'
    message: str


class HRAgent:
    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']

    SYSTEM_INSTRUCTION: str = (
        'You are an agent who handles external verification requests about Staff0'
        ' employees made by third parties.Do not attempt to answer unrelated'
        ' questions or use tools for other purposes.If you are asked about a'
        " person's employee status using their employee ID, use the"
        ' `is_active_employee` tool.If they provide a work email instead, first'
        ' call the `get_employee_id_by_email` tool to get the employee ID, and'
        ' then use `is_active_employee`.'
    )

    RESPONSE_FORMAT_INSTRUCTION: str = (
        'Set the status to "completed" if the request has been fully'
        ' processed.Set the status to "input-required" if the tool response'
        ' indicates that user input is needed to proceed.If the tool response'
        ' contains an AccessDeniedInterrupt error, set the message to "The user'
        ' denied the authorization request", and set the status to "failed".For'
        ' any other tool error, set the status to "failed".'
    )

    def __init__(self):
        self.model = ChatGoogleGenerativeAI(model='gemini-2.0-flash')
        self.tools = [
            get_employee_id_by_email,
            with_async_user_confirmation(is_active_employee),
        ]

        self.graph = create_react_agent(
            self.model,
            tools=self.tools,
            checkpointer=MemorySaver(),
            prompt=self.SYSTEM_INSTRUCTION,
            response_format=(self.RESPONSE_FORMAT_INSTRUCTION, ResponseFormat),
        )

    async def invoke(self, query: str, context_id: str) -> dict[str, Any]:
        config: RunnableConfig = {'configurable': {'thread_id': context_id}}
        await self.graph.ainvoke({'messages': [('user', query)]}, config)
        return self.get_agent_response(config)

    async def stream(
        self, query: str, context_id: str
    ) -> AsyncIterable[dict[str, Any]]:
        inputs: dict[str, Any] = {'messages': [('user', query)]}
        config: RunnableConfig = {'configurable': {'thread_id': context_id}}

        async for item in self.graph.astream(
            inputs, config, stream_mode='values'
        ):
            message = item['messages'][-1] if 'messages' in item else None
            if message:
                if (
                    isinstance(message, AIMessage)
                    and message.tool_calls
                    and len(message.tool_calls) > 0
                ):
                    yield {
                        'is_task_complete': False,
                        'task_state': 'working',
                        'content': 'Looking up the employment status...',
                    }
                elif isinstance(message, ToolMessage):
                    yield {
                        'is_task_complete': False,
                        'task_state': 'working',
                        'content': 'Processing the employment status...',
                    }

        yield self.get_agent_response(config)

    def get_agent_response(self, config: RunnableConfig) -> dict[str, Any]:
        current_state = self.graph.get_state(config)
        structured_response = current_state.values.get('structured_response')

        if structured_response and isinstance(
            structured_response, ResponseFormat
        ):
            return {
                'is_task_complete': structured_response.status == 'completed',
                'task_state': structured_response.status,
                'content': structured_response.message,
            }

        return {
            'is_task_complete': False,
            'task_state': 'unknown',
            'content': (
                'We are unable to process your request at the moment. Please try'
                ' again.'
            ),
        }
