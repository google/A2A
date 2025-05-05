import json

from typing import Any

import httpx

from service.types import (
    AgentClientHTTPError,
    AgentClientJSONError,
    CreateConversationRequest,
    CreateConversationResponse,
    GetEventRequest,
    GetEventResponse,
    JSONRPCRequest,
    ListAgentRequest,
    ListAgentResponse,
    ListConversationRequest,
    ListConversationResponse,
    ListMessageRequest,
    ListMessageResponse,
    ListTaskRequest,
    ListTaskResponse,
    PendingMessageRequest,
    PendingMessageResponse,
    RegisterAgentRequest,
    RegisterAgentResponse,
    SendMessageRequest,
    SendMessageResponse,
)


class ConversationClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')

    async def send_message(
        self, payload: SendMessageRequest
    ) -> SendMessageResponse:
        return SendMessageResponse(**await self._send_request(payload))

    async def _send_request(self, request: JSONRPCRequest) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.base_url + '/' + request.method,
                    json=request.model_dump(),
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise AgentClientHTTPError(
                    e.response.status_code, str(e)
                ) from e
            except json.JSONDecodeError as e:
                raise AgentClientJSONError(str(e)) from e

    async def create_conversation(
        self, payload: CreateConversationRequest
    ) -> CreateConversationResponse:
        return CreateConversationResponse(**await self._send_request(payload))

    async def list_conversation(
        self, payload: ListConversationRequest
    ) -> ListConversationResponse:
        return ListConversationResponse(**await self._send_request(payload))

    async def get_events(self, payload: GetEventRequest) -> GetEventResponse:
        return GetEventResponse(**await self._send_request(payload))

    async def list_messages(
        self, payload: ListMessageRequest
    ) -> ListMessageResponse:
        return ListMessageResponse(**await self._send_request(payload))

    async def get_pending_messages(
        self, payload: PendingMessageRequest
    ) -> PendingMessageResponse:
        return PendingMessageResponse(**await self._send_request(payload))

    async def list_tasks(self, payload: ListTaskRequest) -> ListTaskResponse:
        return ListTaskResponse(**await self._send_request(payload))

    async def register_agent(
        self, payload: RegisterAgentRequest
    ) -> RegisterAgentResponse:
        return RegisterAgentResponse(**await self._send_request(payload))

    async def list_agents(self, payload: ListAgentRequest) -> ListAgentResponse:
        return ListAgentResponse(**await self._send_request(payload))
