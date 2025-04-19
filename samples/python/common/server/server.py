import json
import logging
from typing import AsyncIterable, Any, Dict

from pydantic import ValidationError
from sse_starlette.sse import EventSourceResponse
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse

from A2A.samples.python.common.server.task_manager import TaskManager
from A2A.samples.python.common.types import (
    A2ARequest,
    JSONRPCResponse,
    InvalidRequestError,
    JSONParseError,
    GetTaskRequest,
    CancelTaskRequest,
    SendTaskRequest,
    SetTaskPushNotificationRequest,
    GetTaskPushNotificationRequest,
    InternalError,
    AgentCard,
    TaskResubscriptionRequest,
    SendTaskStreamingRequest,
    # New Knowledge Types
    KnowledgeQueryRequest,
    KnowledgeUpdateRequest,
    KnowledgeSubscribeRequest,
    # Base error type
    MethodNotFoundError, InvalidParamsError, UnsupportedOperationError,
)

# Optional: Define a distinct KnowledgeManager interface if desired
# from common.server.knowledge_manager import KnowledgeManager

logger = logging.getLogger(__name__)


class A2AServer:
    def __init__(
            self,
            host="0.0.0.0",
            port=5000,
            endpoint="/",
            agent_card: AgentCard = None,
            task_manager: TaskManager = None,
            # Optional: Add Knowledge Manager if separating concerns
            # knowledge_manager: KnowledgeManager = None,
    ):
        self.host = host
        self.port = port
        self.endpoint = endpoint
        self.task_manager = task_manager
        self.agent_card = agent_card
        # Store knowledge manager if provided. Assume TaskManager handles it for now.
        # self.knowledge_manager = knowledge_manager or task_manager # If TaskManager implements both
        self.app = Starlette()
        self.app.add_route(self.endpoint, self._process_request, methods=["POST"])
        self.app.add_route(
            "/.well-known/agent.json", self._get_agent_card, methods=["GET"]
        )

    def start(self):
        if self.agent_card is None:
            raise ValueError("agent_card is not defined")

        if self.task_manager is None:
            # Check if the TaskManager instance *also* handles knowledge methods if needed
            # This check might be more complex depending on architecture choice
            raise ValueError("task_manager is not defined")

        # Optional check if KG features are advertised but not implemented
        # if self.agent_card.capabilities.knowledgeGraph and not hasattr(self.task_manager, 'on_knowledge_query'):
        #     raise ValueError("Agent card advertises knowledgeGraph capabilities, but the manager does not implement required methods.")

        import uvicorn

        uvicorn.run(self.app, host=self.host, port=self.port, log_level="info")

    def _get_agent_card(self, request: Request) -> JSONResponse:
        return JSONResponse(self.agent_card.model_dump(exclude_none=True))

    async def _process_request(self, request: Request):
        request_id = None  # Keep track of ID for error responses if parsing fails early
        body = None
        try:
            body = await request.json()
            # Store ID early in case validation fails
            request_id = body.get("id") if isinstance(body, dict) else None
            json_rpc_request = A2ARequest.validate_python(body)
            request_id = json_rpc_request.id  # Get validated ID

            result: Any = None  # To store response or async iterable

            # --- Task Methods ---
            if isinstance(json_rpc_request, GetTaskRequest):
                result = await self.task_manager.on_get_task(json_rpc_request)
            elif isinstance(json_rpc_request, SendTaskRequest):
                result = await self.task_manager.on_send_task(json_rpc_request)
            elif isinstance(json_rpc_request, SendTaskStreamingRequest):
                if not self.agent_card.capabilities.streaming:
                    raise MethodNotFoundError(data={"method": json_rpc_request.method})
                result = await self.task_manager.on_send_task_subscribe(json_rpc_request)
            elif isinstance(json_rpc_request, CancelTaskRequest):
                result = await self.task_manager.on_cancel_task(json_rpc_request)
            elif isinstance(json_rpc_request, SetTaskPushNotificationRequest):
                if not self.agent_card.capabilities.pushNotifications:
                    raise MethodNotFoundError(data={"method": json_rpc_request.method})
                result = await self.task_manager.on_set_task_push_notification(json_rpc_request)
            elif isinstance(json_rpc_request, GetTaskPushNotificationRequest):
                if not self.agent_card.capabilities.pushNotifications:
                    raise MethodNotFoundError(data={"method": json_rpc_request.method})
                result = await self.task_manager.on_get_task_push_notification(json_rpc_request)
            elif isinstance(json_rpc_request, TaskResubscriptionRequest):
                if not self.agent_card.capabilities.streaming:  # Resub requires streaming
                    raise MethodNotFoundError(data={"method": json_rpc_request.method})
                result = await self.task_manager.on_resubscribe_to_task(json_rpc_request)

            # --- Knowledge Methods ---
            elif isinstance(json_rpc_request, KnowledgeQueryRequest):
                if not self.agent_card.capabilities.knowledgeGraph:
                    raise MethodNotFoundError(data={"method": json_rpc_request.method})
                # Assumes TaskManager implements these or routes them
                result = await self.task_manager.on_knowledge_query(json_rpc_request)
            elif isinstance(json_rpc_request, KnowledgeUpdateRequest):
                if not self.agent_card.capabilities.knowledgeGraph:
                    raise MethodNotFoundError(data={"method": json_rpc_request.method})
                result = await self.task_manager.on_knowledge_update(json_rpc_request)
            elif isinstance(json_rpc_request, KnowledgeSubscribeRequest):
                if not self.agent_card.capabilities.knowledgeGraph or not self.agent_card.capabilities.streaming:
                    raise MethodNotFoundError(data={"method": json_rpc_request.method})
                result = await self.task_manager.on_knowledge_subscribe(json_rpc_request)

            # --- Fallback ---
            else:
                # This case should ideally not be reached due to A2ARequest validation
                logger.warning(f"Unexpected validated request type: {type(json_rpc_request)}")
                raise MethodNotFoundError(data={"method": body.get("method", "unknown") if body else "unknown"})

            # Create and return the response
            return self._create_response(result)

        except MethodNotFoundError as e:
            # Specific handling for unsupported methods based on capabilities
            logger.warning(f"Method not found or not supported by agent capabilities: {e.data.get('method')}")
            response = JSONRPCResponse(id=request_id, error=e)
            return JSONResponse(response.model_dump(exclude_none=True), status_code=404)  # 404 Not Found might be appropriate

        except json.JSONDecodeError as e:
            logger.error(f"JSON Parsing Error: {e}", exc_info=True)
            json_rpc_error = JSONParseError(data=str(e))  # Include original error string
            response = JSONRPCResponse(id=request_id, error=json_rpc_error)
            # Use 400 Bad Request for parse errors
            return JSONResponse(response.model_dump(exclude_none=True), status_code=400)

        except ValidationError as e:
            logger.error(f"Request Validation Error: {e.errors()}", exc_info=False)  # Don't need full stack trace usually
            # Provide detailed validation errors in the 'data' field
            json_rpc_error = InvalidRequestError(data=e.errors())
            response = JSONRPCResponse(id=request_id, error=json_rpc_error)
            # Use 400 Bad Request for validation errors
            return JSONResponse(response.model_dump(exclude_none=True), status_code=400)

        except NotImplementedError as e:  # Catch explicit NotImplemented from manager
            logger.warning(f"Operation not implemented by manager: {e}")
            json_rpc_error = UnsupportedOperationError(message=str(e))
            response = JSONRPCResponse(id=request_id, error=json_rpc_error)
            return JSONResponse(response.model_dump(exclude_none=True), status_code=501)  # 501 Not Implemented

        except Exception as e:
            # Catch-all for unexpected internal errors
            logger.error(f"Unhandled Internal Server Error: {e}", exc_info=True)
            json_rpc_error = InternalError(data=str(e))  # Include error string in data
            response = JSONRPCResponse(id=request_id, error=json_rpc_error)
            # Use 500 Internal Server Error
            return JSONResponse(response.model_dump(exclude_none=True), status_code=500)

    def _handle_exception(self, e: Exception, request_id: str | int | None = None) -> JSONResponse:
        # This function becomes less used with the more specific error handling in _process_request,
        # but kept as a fallback.
        logger.error(f"Exception caught in _handle_exception: {e}", exc_info=True)
        if isinstance(e, json.decoder.JSONDecodeError):
            json_rpc_error = JSONParseError(data=str(e))
            status_code = 400
        elif isinstance(e, ValidationError):
            json_rpc_error = InvalidRequestError(data=e.errors())
            status_code = 400
        elif isinstance(e, MethodNotFoundError):
            json_rpc_error = e
            status_code = 404
        elif isinstance(e, NotImplementedError):
            json_rpc_error = UnsupportedOperationError(message=str(e))
            status_code = 501
        else:
            json_rpc_error = InternalError(data=str(e))
            status_code = 500

        response = JSONRPCResponse(id=request_id, error=json_rpc_error)
        return JSONResponse(response.model_dump(exclude_none=True), status_code=status_code)

    def _create_response(self, result: Any) -> JSONResponse | EventSourceResponse:
        if isinstance(result, AsyncIterable):
            # This handles streaming responses (tasks/sendSubscribe, knowledge/subscribe)
            async def event_generator(result_iterable) -> AsyncIterable[Dict[str, str]]:
                async for item in result_iterable:
                    if isinstance(item, JSONRPCResponse):  # Check if it's a JSONRPCResponse (might contain error or result)
                        yield {"data": item.model_dump_json(exclude_none=True)}
                    else:
                        # Fallback or handle other potential yielded types if necessary
                        logger.warning(f"Unexpected type yielded in streaming response: {type(item)}")
                        # Optionally yield an error event
                        error_response = JSONRPCResponse(error=InternalError(message=f"Unexpected stream item type: {type(item)}"))
                        yield {"data": error_response.model_dump_json(exclude_none=True)}

            return EventSourceResponse(event_generator(result))
        elif isinstance(result, JSONRPCResponse):
            # Standard JSON-RPC response for non-streaming methods
            # Determine status code based on whether it's an error or success
            status_code = 400 if result.error else 200
            # Refine status code for specific errors if possible
            if result.error:
                if result.error.code == MethodNotFoundError.code:
                    status_code = 404
                elif result.error.code == InvalidRequestError.code or result.error.code == InvalidParamsError.code:
                    status_code = 400
                elif result.error.code == InternalError.code:
                    status_code = 500
                # Add more specific codes if needed (e.g., 501 for UnsupportedOperationError)

            return JSONResponse(result.model_dump(exclude_none=True), status_code=status_code)
        else:
            # Should not happen if handlers return correctly
            logger.error(f"Unexpected result type from handler: {type(result)}")
            internal_error = InternalError(message=f"Handler returned unexpected type: {type(result)}")
            error_response = JSONRPCResponse(error=internal_error)
            return JSONResponse(error_response.model_dump(exclude_none=True), status_code=500)
