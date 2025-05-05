import json
import random

from typing import Any

from google.adk.agents.llm_agent import LlmAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.tool_context import ToolContext
from task_manager import AgentWithTaskManager


# Local cache of created request_ids for demo purposes.
request_ids = set()


def create_request_form(
    date: str | None = None,
    amount: str | None = None,
    purpose: str | None = None,
) -> dict[str, Any]:
    """Create a request form for the employee to fill out.

    Args:
        date (str): The date of the request. Can be an empty string.
        amount (str): The requested amount. Can be an empty string.
        purpose (str): The purpose of the request. Can be an empty string.

    Returns:
        dict[str, Any]: A dictionary containing the request form data.
    """
    request_id = 'request_id_' + str(random.randint(1000000, 9999999))
    request_ids.add(request_id)
    return {
        'request_id': request_id,
        'date': '<transaction date>' if not date else date,
        'amount': '<transaction dollar amount>' if not amount else amount,
        'purpose': '<business justification/purpose of the transaction>'
        if not purpose
        else purpose,
    }


def return_form(
    form_request: dict[str, Any],
    tool_context: ToolContext,
    instructions: str | None = None,
) -> dict[str, Any]:
    """Returns a structured json object indicating a form to complete.

    Args:
        form_request (dict[str, Any]): The request form data.
        tool_context (ToolContext): The context in which the tool operates.
        instructions (str): Instructions for processing the form. Can be an empty string.

    Returns:
        dict[str, Any]: A JSON dictionary for the form response.
    """
    if isinstance(form_request, str):
        form_request = json.loads(form_request)

    tool_context.actions.skip_summarization = True
    tool_context.actions.escalate = True
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
    return json.dumps(form_dict)


def reimburse(request_id: str) -> dict[str, Any]:
    """Reimburse the amount of money to the employee for a given request_id."""
    if request_id not in request_ids:
        return {
            'request_id': request_id,
            'status': 'Error: Invalid request_id.',
        }
    return {'request_id': request_id, 'status': 'approved'}


class ReimbursementAgent(AgentWithTaskManager):
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

    def get_processing_message(self) -> str:
        return 'Processing the reimbursement request...'

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
    You are an agent who handles the reimbursement process for employees.

    When you receive a reimbursement request, you should first create a new request form using create_request_form(). Only provide default values if they are provided by the user, otherwise use an empty string as the default value.
      1. 'Date': the date of the transaction.
      2. 'Amount': the dollar amount of the transaction.
      3. 'Business Justification/Purpose': the reason for the reimbursement.

    Once you created the form, you should return the result of calling return_form with the form data from the create_request_form call.

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
