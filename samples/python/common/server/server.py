
from starlette.applications import Starlette
from starlette.responses import JSONResponse, HTMLResponse

import json
import logging

from collections.abc import AsyncIterable
from typing import Any

from pydantic import ValidationError

from sse_starlette.sse import EventSourceResponse
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse

from common.server.task_manager import TaskManager
from common.types import (
    A2ARequest,
    AgentCard,
    CancelTaskRequest,
    GetTaskPushNotificationRequest,
    GetTaskRequest,
    InternalError,
    InvalidRequestError,
    JSONParseError,
    JSONRPCResponse,
    SendTaskRequest,
    SendTaskStreamingRequest,
    SetTaskPushNotificationRequest,
    TaskResubscriptionRequest,
)


logger = logging.getLogger(__name__)


class A2AServer:
    def __init__(
        self,
        host='0.0.0.0',
        port=5000,
        endpoint='/',
        agent_card: AgentCard = None,
        task_manager: TaskManager = None,
    ):
        self.host = host
        self.port = port
        self.endpoint = endpoint
        self.task_manager = task_manager
        self.agent_card = agent_card
        self.app = Starlette()

        self.app.add_route(self.endpoint, self._process_request, methods=["POST"])
        self.app.add_route(self.endpoint, self._handle_root_get, methods=["GET"])

        self.app.add_route(
            self.endpoint, self._process_request, methods=['POST']
        )
        self.app.add_route(
            '/.well-known/agent.json', self._get_agent_card, methods=['GET']
        )

    def start(self):
        if self.agent_card is None:
            raise ValueError('agent_card is not defined')

        if self.task_manager is None:
            raise ValueError('request_handler is not defined')

        import uvicorn

        logger.info(f"Starting A2A server at http://{self.host}:{self.port}")
        logger.info(f"Agent Card available at http://{self.host}:{self.port}/.well-known/agent.json")
        uvicorn.run(self.app, host=self.host, port=self.port)

    def _get_agent_card(self, request: Request) -> JSONResponse:
        return JSONResponse(self.agent_card.model_dump(exclude_none=True))
    
    async def _handle_root_get(self, request: Request) -> HTMLResponse:
        """Handle GET requests to the root endpoint with a helpful message."""
        agent_name = self.agent_card.name if self.agent_card else "A2A Agent"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{agent_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: 0 auto; }}
                h1 {{ color: #333; }}
                code {{ background-color: #f4f4f4; padding: 2px 4px; border-radius: 4px; }}
                .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin-top: 20px; }}
                .note {{ background-color: #f8f9fa; padding: 10px; border-left: 4px solid #007bff; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>🤖 {agent_name}</h1>
            <p>This is an <strong>A2A (Agent-to-Agent) protocol</strong> endpoint. Direct browser access is not supported.</p>
            
            <div class="note">
                <p>The Agent Card is available at: <a href="/.well-known/agent.json">/.well-known/agent.json</a></p>
            </div>
            
            <h2>How to interact with this agent:</h2>
            <ol>
                <li>Use an A2A client like the CLI tool or demo web UI</li>
                <li>Send POST requests to this endpoint with proper A2A protocol messages</li>
                <li>Refer to the <a href="https://google.github.io/A2A/#/documentation">A2A documentation</a> for protocol details</li>
            </ol>
            
            <div class="card">
                <h3>API Endpoints:</h3>
                <ul>
                    <li><code>GET /.well-known/agent.json</code> - Agent Card (capabilities, metadata)</li>
                    <li><code>POST /</code> - A2A Protocol interactions (tasks/send, tasks/get, etc.)</li>
                </ul>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    async def _process_request(self, request: Request):
        try:
            body = await request.json()
            json_rpc_request = A2ARequest.validate_python(body)

            if isinstance(json_rpc_request, GetTaskRequest):
                result = await self.task_manager.on_get_task(json_rpc_request)
            elif isinstance(json_rpc_request, SendTaskRequest):
                result = await self.task_manager.on_send_task(json_rpc_request)
            elif isinstance(json_rpc_request, SendTaskStreamingRequest):
                result = await self.task_manager.on_send_task_subscribe(
                    json_rpc_request
                )
            elif isinstance(json_rpc_request, CancelTaskRequest):
                result = await self.task_manager.on_cancel_task(
                    json_rpc_request
                )
            elif isinstance(json_rpc_request, SetTaskPushNotificationRequest):
                result = await self.task_manager.on_set_task_push_notification(
                    json_rpc_request
                )
            elif isinstance(json_rpc_request, GetTaskPushNotificationRequest):
                result = await self.task_manager.on_get_task_push_notification(
                    json_rpc_request
                )
            elif isinstance(json_rpc_request, TaskResubscriptionRequest):
                result = await self.task_manager.on_resubscribe_to_task(
                    json_rpc_request
                )
            else:
                logger.warning(
                    f'Unexpected request type: {type(json_rpc_request)}'
                )
                raise ValueError(f'Unexpected request type: {type(request)}')

            return self._create_response(result)

        except Exception as e:
            return self._handle_exception(e)

    def _handle_exception(self, e: Exception) -> JSONResponse:
        if isinstance(e, json.decoder.JSONDecodeError):
            json_rpc_error = JSONParseError()
        elif isinstance(e, ValidationError):
            json_rpc_error = InvalidRequestError(data=json.loads(e.json()))
        else:
            logger.error(f'Unhandled exception: {e}')
            json_rpc_error = InternalError()

        response = JSONRPCResponse(id=None, error=json_rpc_error)
        return JSONResponse(
            response.model_dump(exclude_none=True), status_code=400
        )

    def _create_response(
        self, result: Any
    ) -> JSONResponse | EventSourceResponse:
        if isinstance(result, AsyncIterable):

            async def event_generator(result) -> AsyncIterable[dict[str, str]]:
                async for item in result:
                    yield {'data': item.model_dump_json(exclude_none=True)}

            return EventSourceResponse(event_generator(result))
        if isinstance(result, JSONRPCResponse):
            return JSONResponse(result.model_dump(exclude_none=True))
        logger.error(f'Unexpected result type: {type(result)}')
        raise ValueError(f'Unexpected result type: {type(result)}')
