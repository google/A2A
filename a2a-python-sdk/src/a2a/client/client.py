import json

from collections.abc import AsyncGenerator
from typing import Any
from uuid import uuid4

import httpx

from httpx_sse import SSEError, aconnect_sse

from a2a.client.errors import A2AClientHTTPError, A2AClientJSONError
from a2a.types import (
    A2ARequest,
    AgentCard,
    CancelTaskRequest,
    CancelTaskResponse,
    GetTaskPushNotificationConfigRequest,
    GetTaskPushNotificationConfigResponse,
    GetTaskRequest,
    GetTaskResponse,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageStreamingRequest,
    SendMessageStreamingResponse,
    SetTaskPushNotificationConfigRequest,
    SetTaskPushNotificationConfigResponse,
    TaskIdParams,
    TaskPushNotificationConfig,
    TaskQueryParams,
)


class A2ACardResolver:
    """Agent Card resolver."""

    def __init__(
        self,
        httpx_client: httpx.AsyncClient,
        base_url: str,
        agent_card_path: str = '/.well-known/agent.json',
    ):
        self.base_url = base_url.rstrip('/')
        self.agent_card_path = agent_card_path.lstrip('/')
        self.httpx_client = httpx_client

    async def get_agent_card(self) -> AgentCard:
        try:
            response = await self.httpx_client.get(
                f'{self.base_url}/{self.agent_card_path}'
            )
            response.raise_for_status()
            return AgentCard.model_validate(response.json())
        except httpx.HTTPStatusError as e:
            raise A2AClientHTTPError(e.response.status_code, str(e)) from e
        except json.JSONDecodeError as e:
            raise A2AClientJSONError(str(e)) from e
        except httpx.RequestError as e:
            raise A2AClientHTTPError(
                503, f'Network communication error: {e}'
            ) from e


class A2AClient:
    """A2A Client."""

    def __init__(
        self,
        httpx_client: httpx.AsyncClient,
        agent_card: AgentCard | None = None,
        url: str | None = None,
    ):
        if agent_card:
            self.url = agent_card.url
        elif url:
            self.url = url
        else:
            raise ValueError('Must provide either agent_card or url')

        self.httpx_client = httpx_client

    @classmethod
    async def get_client_from_agent_card_url(
        cls,
        httpx_client: httpx.AsyncClient,
        base_url: str,
        agent_card_path: str = '/.well-known/agent.json',
    ) -> 'A2AClient':
        """Get a A2A client for provided agent card URL."""
        agent_card: AgentCard = await A2ACardResolver(
            httpx_client, base_url=base_url, agent_card_path=agent_card_path
        ).get_agent_card()
        return A2AClient(httpx_client=httpx_client, agent_card=agent_card)

    async def send_message(
        self, payload: dict[str, Any], request_id: str | int = uuid4().hex
    ) -> SendMessageResponse:
        request = SendMessageRequest(
            id=request_id, params=MessageSendParams.model_validate(payload)
        )
        return SendMessageResponse(
            **await self._send_request(A2ARequest(root=request))
        )

    async def send_message_streaming(
        self, payload: dict[str, Any], request_id: str | int = uuid4().hex
    ) -> AsyncGenerator[SendMessageStreamingResponse, None]:
        request = SendMessageStreamingRequest(
            id=request_id, params=MessageSendParams.model_validate(payload)
        )
        async with aconnect_sse(
            self.httpx_client,
            'POST',
            self.url,
            json=request.model_dump(mode='json'),
            timeout=None,
        ) as event_source:
            try:
                async for sse in event_source.aiter_sse():
                    yield SendMessageStreamingResponse(**json.loads(sse.data))
            except SSEError as e:
                raise A2AClientHTTPError(
                    400, f'Invalid SSE response or protocol error: {e}'
                ) from e
            except json.JSONDecodeError as e:
                raise A2AClientJSONError(str(e)) from e
            except httpx.RequestError as e:
                raise A2AClientHTTPError(
                    503, f'Network communication error: {e}'
                ) from e

    async def _send_request(self, request: A2ARequest) -> dict[str, Any]:
        try:
            response = await self.httpx_client.post(
                self.url, json=request.root.model_dump(mode='json')
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise A2AClientHTTPError(e.response.status_code, str(e)) from e
        except json.JSONDecodeError as e:
            raise A2AClientJSONError(str(e)) from e

    async def get_task(
        self, payload: dict[str, Any], request_id: str | int = uuid4().hex
    ) -> GetTaskResponse:
        request = GetTaskRequest(
            id=request_id, params=TaskQueryParams.model_validate(payload)
        )
        return GetTaskResponse(
            **await self._send_request(A2ARequest(root=request))
        )

    async def cancel_task(
        self, payload: dict[str, Any], request_id: str | int = uuid4().hex
    ) -> CancelTaskResponse:
        request = CancelTaskRequest(
            id=request_id, params=TaskIdParams.model_validate(payload)
        )
        return CancelTaskResponse(
            **await self._send_request(A2ARequest(root=request))
        )

    async def set_task_callback(
        self, payload: dict[str, Any], request_id: str | int = uuid4().hex
    ) -> SetTaskPushNotificationConfigResponse:
        request = SetTaskPushNotificationConfigRequest(
            id=request_id,
            params=TaskPushNotificationConfig.model_validate(payload),
        )
        return SetTaskPushNotificationConfigResponse(
            **await self._send_request(A2ARequest(root=request))
        )

    async def get_task_callback(
        self, payload: dict[str, Any], request_id: str | int = uuid4().hex
    ) -> GetTaskPushNotificationConfigResponse:
        request = GetTaskPushNotificationConfigRequest(
            id=request_id, params=TaskIdParams.model_validate(payload)
        )
        return GetTaskPushNotificationConfigResponse(
            **await self._send_request(A2ARequest(root=request))
        )
