import json
from typing import Any, AsyncIterable, Dict

import httpx
from httpx_sse import connect_sse

from A2A.samples.python.common.types import (
    AgentCard,
    AgentCapabilities,
    GetTaskRequest,
    SendTaskRequest,
    SendTaskResponse,
    JSONRPCRequest,
    GetTaskResponse,
    CancelTaskResponse,
    CancelTaskRequest,
    SetTaskPushNotificationRequest,
    SetTaskPushNotificationResponse,
    GetTaskPushNotificationRequest,
    GetTaskPushNotificationResponse,
    A2AClientHTTPError,
    A2AClientJSONError,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    # New Knowledge Types
    KnowledgeQueryRequest,
    KnowledgeQueryResponse,
    KnowledgeUpdateRequest,
    KnowledgeUpdateResponse,
    KnowledgeSubscribeRequest,
    KnowledgeSubscriptionEvent,  # Note: This is the event type, not the full response wrapper
)


class A2AClient:
    def __init__(self, agent_card: AgentCard = None, url: str = None):
        if agent_card:
            self.url = agent_card.url
            self.agent_capabilities = agent_card.capabilities
        elif url:
            self.url = url
            # Attempt to fetch capabilities, or assume defaults
            # For simplicity here, we'll assume default capabilities if no card
            # In a real scenario, you might fetch the card here.
            self.agent_capabilities = AgentCapabilities()  # Default caps
        else:
            raise ValueError("Must provide either agent_card or url")

    async def send_task(self, payload: Dict[str, Any]) -> SendTaskResponse:
        request = SendTaskRequest(params=payload)
        response_data = await self._send_request(request)
        return SendTaskResponse(**response_data)

    async def send_task_streaming(
            self, payload: Dict[str, Any]
    ) -> AsyncIterable[SendTaskStreamingResponse]:
        if not self.agent_capabilities.streaming:
            raise NotImplementedError("Agent does not support streaming (tasks/sendSubscribe)")
        request = SendTaskStreamingRequest(params=payload)
        # Use a shared client for potential connection reuse within the stream
        async with httpx.AsyncClient(timeout=None) as client:
            try:
                async with connect_sse(
                        client, "POST", self.url, json=request.model_dump(exclude_none=True)
                ) as event_source:
                    async for sse in event_source.aiter_sse():
                        try:
                            # Each SSE data payload should be a full JSONRPCResponse structure
                            # containing the streaming event in its 'result' field.
                            yield SendTaskStreamingResponse(**json.loads(sse.data))
                        except json.JSONDecodeError as e:
                            # Yield an error structure if parsing fails for an event
                            yield SendTaskStreamingResponse(
                                id=request.id,  # Use original request ID
                                error=A2AClientJSONError(f"Failed to decode SSE data: {sse.data}, error: {e}")
                            )
                            # Depending on desired behavior, you might break or continue
                            # break # Option: Stop stream on first error
                        except Exception as e:  # Catch other validation/processing errors
                            yield SendTaskStreamingResponse(
                                id=request.id,
                                error=A2AClientJSONError(f"Error processing SSE data: {sse.data}, error: {e}")
                            )
                            # break # Option: Stop stream on first error

            except httpx.RequestError as e:
                # This exception happens if the initial connection fails
                raise A2AClientHTTPError(getattr(e, 'response', None).status_code if hasattr(e, 'response') else 400, str(e)) from e
            except httpx.HTTPStatusError as e:
                # This catches non-2xx responses for the initial connection
                raise A2AClientHTTPError(e.response.status_code, str(e)) from e

    async def _send_request(self, request: JSONRPCRequest) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                # Image generation could take time, adding timeout
                # TODO: Make timeout configurable or context-dependent
                response = await client.post(
                    self.url, json=request.model_dump(exclude_none=True), timeout=60
                )
                response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx
                return response.json()
            except httpx.HTTPStatusError as e:
                # Attempt to parse error response body for more details
                try:
                    error_details = e.response.json()
                except json.JSONDecodeError:
                    error_details = e.response.text
                raise A2AClientHTTPError(e.response.status_code, f"{str(e)} - Body: {error_details}") from e
            except json.JSONDecodeError as e:
                # Response was likely not valid JSON
                raise A2AClientJSONError(f"{str(e)} - Received non-JSON response: {response.text}") from e
            except httpx.RequestError as e:
                # General connection errors (DNS, connection refused, etc.)
                raise A2AClientHTTPError(400, str(e)) from e

    async def get_task(self, payload: Dict[str, Any]) -> GetTaskResponse:
        request = GetTaskRequest(params=payload)
        response_data = await self._send_request(request)
        return GetTaskResponse(**response_data)

    async def cancel_task(self, payload: Dict[str, Any]) -> CancelTaskResponse:
        request = CancelTaskRequest(params=payload)
        response_data = await self._send_request(request)
        return CancelTaskResponse(**response_data)

    async def set_task_callback(
            self, payload: Dict[str, Any]
    ) -> SetTaskPushNotificationResponse:
        if not self.agent_capabilities.pushNotifications:
            raise NotImplementedError("Agent does not support push notifications (tasks/pushNotification/set)")
        request = SetTaskPushNotificationRequest(params=payload)
        response_data = await self._send_request(request)
        return SetTaskPushNotificationResponse(**response_data)

    async def get_task_callback(
            self, payload: Dict[str, Any]
    ) -> GetTaskPushNotificationResponse:
        if not self.agent_capabilities.pushNotifications:
            raise NotImplementedError("Agent does not support push notifications (tasks/pushNotification/get)")
        request = GetTaskPushNotificationRequest(params=payload)
        response_data = await self._send_request(request)
        return GetTaskPushNotificationResponse(**response_data)

    # --- New Knowledge Graph Methods ---

    async def knowledge_query(self, payload: Dict[str, Any]) -> KnowledgeQueryResponse:
        """
        Sends a knowledge query (e.g., GraphQL) to the agent.
        """
        if not self.agent_capabilities.knowledgeGraph:
            raise NotImplementedError("Agent does not support knowledge graph features (knowledge/query)")
        request = KnowledgeQueryRequest(params=payload)
        response_data = await self._send_request(request)
        return KnowledgeQueryResponse(**response_data)

    async def knowledge_update(self, payload: Dict[str, Any]) -> KnowledgeUpdateResponse:
        """
        Sends proposed updates (patches) to the agent's knowledge graph.
        """
        if not self.agent_capabilities.knowledgeGraph:
            raise NotImplementedError("Agent does not support knowledge graph features (knowledge/update)")
        request = KnowledgeUpdateRequest(params=payload)
        response_data = await self._send_request(request)
        return KnowledgeUpdateResponse(**response_data)

    async def knowledge_subscribe(
            self, payload: Dict[str, Any]
    ) -> AsyncIterable[KnowledgeSubscriptionEvent]:
        """
        Subscribes to changes in the agent's knowledge graph using SSE.
        Yields KnowledgeSubscriptionEvent objects.
        """
        if not self.agent_capabilities.knowledgeGraph or not self.agent_capabilities.streaming:
            raise NotImplementedError(
                "Agent does not support knowledge graph subscriptions (knowledge/subscribe requires knowledgeGraph and streaming capabilities)")

        request = KnowledgeSubscribeRequest(params=payload)
        # Use a shared client for potential connection reuse within the stream
        async with httpx.AsyncClient(timeout=None) as client:
            try:
                async with connect_sse(
                        client, "POST", self.url, json=request.model_dump(exclude_none=True)
                ) as event_source:
                    async for sse in event_source.aiter_sse():
                        try:
                            # Each SSE data payload should be a full JSONRPCResponse structure
                            # containing the KnowledgeGraphChangeEvent in its 'result' field.
                            yield KnowledgeSubscriptionEvent(**json.loads(sse.data))
                        except json.JSONDecodeError as e:
                            yield KnowledgeSubscriptionEvent(
                                id=request.id,  # Use original request ID
                                error=A2AClientJSONError(f"Failed to decode SSE data: {sse.data}, error: {e}")
                            )
                            # break # Option: Stop stream on first error
                        except Exception as e:  # Catch other validation/processing errors
                            yield KnowledgeSubscriptionEvent(
                                id=request.id,
                                error=A2AClientJSONError(f"Error processing SSE data: {sse.data}, error: {e}")
                            )
                            # break # Option: Stop stream on first error

            except httpx.RequestError as e:
                raise A2AClientHTTPError(getattr(e, 'response', None).status_code if hasattr(e, 'response') else 400, str(e)) from e
            except httpx.HTTPStatusError as e:
                raise A2AClientHTTPError(e.response.status_code, str(e)) from e
