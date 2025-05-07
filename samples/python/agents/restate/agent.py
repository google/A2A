"""An agent that handles reimbursement requests. Pretty much a copy of the
reimbursement agent from this repo, just made the tools a bit more interesting.
"""

import json
import logging
import random

from typing import Any, Optional

from agents.restate.middleware import AgentInvokeResult
from common.types import TextPart
from google.adk.agents.llm_agent import LlmAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.tool_context import ToolContext
from google.genai import types


logger = logging.getLogger(__name__)


# Local cache of created request_ids for demo purposes.
request_ids = set()


def create_request_form(
    date: Optional[str] = None,
    amount: Optional[str] = None,
    purpose: Optional[str] = None,
) -> dict[str, Any]:
    """Create a request form for the employee to fill out.

    Args:
        date (str): The date of the request. Can be an empty string.
        amount (str): The requested amount. Can be an empty string.
        purpose (str): The purpose of the request. Can be an empty string.

    Returns:
        dict[str, Any]: A dictionary containing the request form data.
    """
    logger.info('Creating reimbursement request')
    request_id = 'request_id_' + str(random.randint(1000000, 9999999))
    request_ids.add(request_id)
    reimbursement = {
        'request_id': request_id,
        'date': '<transaction date>' if not date else date,
        'amount': '<transaction dollar amount>' if not amount else amount,
        'purpose': (
            '<business justification/purpose of the transaction>'
            if not purpose
            else purpose
        ),
    }
    logger.info('Reimbursement request created: %s', json.dumps(reimbursement))

    return reimbursement


def return_form(
    form_request: dict[str, Any],
    tool_context: ToolContext,
    instructions: Optional[str] = None,
) -> dict[str, Any]:
    """Returns a structured json object indicating a form to complete.

    Args:
        form_request (dict[str, Any]): The request form data.
        tool_context (ToolContext): The context in which the tool operates.
        instructions (str): Instructions for processing the form. Can be an empty string.

    Returns:
        dict[str, Any]: A JSON dictionary for the form response.
    """
    logger.info('Creating return form')
    if isinstance(form_request, str):
        form_request = json.loads(form_request)

    form_dict = {
        'type': 'form',
        'form': {
            'type': 'object',
            'properties': {
                'date': {
                    'type': 'string',
                    'format': 'date',
                    'description': 'Date of expense',
                    'title': 'Date',
                },
                'amount': {
                    'type': 'string',
                    'format': 'number',
                    'description': 'Amount of expense',
                    'title': 'Amount',
                },
                'purpose': {
                    'type': 'string',
                    'description': 'Purpose of expense',
                    'title': 'Purpose',
                },
                'request_id': {
                    'type': 'string',
                    'description': 'Request id',
                    'title': 'Request ID',
                },
            },
            'required': list(form_request.keys()),
        },
        'form_data': form_request,
        'instructions': instructions,
    }
    logger.info('Return form created: %s', json.dumps(form_dict))
    return json.dumps(form_dict)


async def reimburse(request_id: str) -> dict[str, Any]:
    """Reimburse the amount of money to the employee for a given request_id."""
    logger.info('Starting reimbursement: %s', request_id)
    if request_id not in request_ids:
        return {
            'request_id': request_id,
            'status': 'Error: Invalid request_id.',
        }
    logger.info('Reimbursement approved: %s', request_id)
    return {'request_id': request_id, 'status': 'approved'}


class ReimbursementAgent:
    """An agent that handles reimbursement requests."""

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']

    def __init__(self):
        self._agent = self._build_agent()
        self._user_id = 'remote_agent'
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    async def invoke(self, query, session_id) -> AgentInvokeResult:
        logger.info('Invoking LLM')
        session = self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )
        content = types.Content(
            role='user', parts=[types.Part.from_text(text=query)]
        )
        if session is None:
            self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )

        events = []
        async for event in self._runner.run_async(
            user_id=self._user_id,
            session_id=session_id,
            new_message=content,
        ):
            events.append(event)

        logger.info('LLM response: %s', events)
        if not events or not events[-1].content or not events[-1].content.parts:
            return AgentInvokeResult(
                parts=[TextPart(text='')],
                require_user_input=False,
                is_task_complete=True,
            )
        return AgentInvokeResult(
            parts=[
                TextPart(
                    text='\n'.join(
                        [p.text for p in events[-1].content.parts if p.text]
                    )
                )
            ],
            require_user_input=False,
            is_task_complete=True,
        )

    def _build_agent(self) -> LlmAgent:
        """Builds the LLM agent for the reimbursement agent."""
        return LlmAgent(
            model='gemini-2.0-flash-001',
            name='reimbursement_agent',
            description=(
                'This agent handles the reimbursement process for the employees'
                ' given the amount and purpose of the reimbursement.'
            ),
            instruction="""
    You are an agent who handle the reimbursement process for employees.

    When you receive an reimbursement request, you should first create a new request form using create_request_form(). Only provide default values if they are provided by the user, otherwise use an empty string as the default value.
      1. 'Date': the date of the transaction.
      2. 'Amount': the dollar amount of the transaction.
      3. 'Business Justification/Purpose': the reason for the reimbursement.

    Once you created the form, you should return the result of calling return_form with the form data from the create_request_form call.
    Clearly let the user know which fields are required and missing. 

    Once you received the filled-out form back from the user, you should then check the form contains all required information:
      1. 'Date': the date of the transaction.
      2. 'Amount': the value of the amount of the reimbursement being requested.
      3. 'Business Justification/Purpose': the item/object/artifact of the reimbursement.

    If you don't have all of the information, you should reject the request directly by calling the request_form method, providing the missing fields.


    For valid reimbursement requests, you can then use reimburse() to reimburse the employee.
      * In your response, you should include the request_id and the status of the reimbursement request.

    """,
            tools=[
                create_request_form,
                reimburse,
                return_form,
            ],
        )
