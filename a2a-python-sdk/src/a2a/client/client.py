import json

from collections.abc import AsyncGenerator
from typing import Any
from uuid import uuid4

import httpx

from httpx_sse import SSEError, aconnect_sse

from a2a.client.errors import A2AClientHTTPError, A2AClientJSONError
from a2a.types import (
    AgentCard,
    CancelTaskRequest,
    CancelTaskResponse,
    GetTaskPushNotificationConfigRequest,
    GetTaskPushNotificationConfigResponse,
    GetTaskRequest,
    GetTaskResponse,
    SendMessageRequest,
    SendMessageResponse,
    SendStreamingMessageRequest,
    SendStreamingMessageResponse,
    SetTaskPushNotificationConfigRequest,
    SetTaskPushNotificationConfigResponse,
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

    async def get_agent_card(
        self, http_kwargs: dict[str, Any] | None = None
    ) -> AgentCard:
        try:
            response = await self.httpx_client.get(
                f'{self.base_url}/{self.agent_card_path}',
                **(http_kwargs or {}),
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

    @staticmethod
    async def get_client_from_agent_card_url(
        httpx_client: httpx.AsyncClient,
        base_url: str,
        agent_card_path: str = '/.well-known/agent.json',
        http_kwargs: dict[str, Any] | None = None,
    ) -> 'A2AClient':
        """Get a A2A client for provided agent card URL."""
        agent_card: AgentCard = await A2ACardResolver(
            httpx_client, base_url=base_url, agent_card_path=agent_card_path
        ).get_agent_card(http_kwargs=http_kwargs)
        return A2AClient(httpx_client=httpx_client, agent_card=agent_card)

    async def send_message(
        self,
        request: SendMessageRequest,
        *,
        http_kwargs: dict[str, Any] | None = None,
    ) -> SendMessageResponse:
        if not request.id:
            request.id = str(uuid4())

        return SendMessageResponse(
            **await self._send_request(
                request.model_dump(mode='json', exclude_none=True),
                http_kwargs,
            )
        )

    async def send_message_streaming(
        self,
        request: SendStreamingMessageRequest,
        *,
        http_kwargs: dict[str, Any] | None = None,
    ) -> AsyncGenerator[SendStreamingMessageResponse, None]:
        if not request.id:
            request.id = str(uuid4())

        # Default to no timeout for streaming, can be overridden by http_kwargs
        http_kwargs_with_timeout: dict[str, Any] = {
            'timeout': None,
            **(http_kwargs or {}),
        }

        async with aconnect_sse(
            self.httpx_client,
            'POST',
            self.url,
            json=request.model_dump(mode='json', exclude_none=True),
            **http_kwargs_with_timeout,
        ) as event_source:
            try:
                async for sse in event_source.aiter_sse():
                    yield SendStreamingMessageResponse(**json.loads(sse.data))
            except SSEError as e:
                raise A2AClientHTTPError(
                    400,
                    f'Invalid SSE response or protocol error: {e}',
                ) from e
            except json.JSONDecodeError as e:
                raise A2AClientJSONError(str(e)) from e
            except httpx.RequestError as e:
                raise A2AClientHTTPError(
                    503, f'Network communication error: {e}'
                ) from e

    async def _send_request(
        self,
        rpc_request_payload: dict[str, Any],
        http_kwargs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Sends a non-streaming JSON-RPC request to the agent.

        Args:
            rpc_request_payload: JSON RPC payload for sending the request
            **kwargs: Additional keyword arguments to pass to the httpx client.
        """
        try:
            response = await self.httpx_client.post(
                self.url, json=rpc_request_payload, **(http_kwargs or {})
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise A2AClientHTTPError(e.response.status_code, str(e)) from e
        except json.JSONDecodeError as e:
            raise A2AClientJSONError(str(e)) from e
        except httpx.RequestError as e:
            raise A2AClientHTTPError(
                503, f'Network communication error: {e}'
            ) from e

    async def get_task(
        self,
        request: GetTaskRequest,
        *,
        http_kwargs: dict[str, Any] | None = None,
    ) -> GetTaskResponse:
        if not request.id:
            request.id = str(uuid4())

        return GetTaskResponse(
            **await self._send_request(
                request.model_dump(mode='json', exclude_none=True),
                http_kwargs,
            )
        )

    async def cancel_task(
        self,
        request: CancelTaskRequest,
        *,
        http_kwargs: dict[str, Any] | None = None,
    ) -> CancelTaskResponse:
        if not request.id:
            request.id = str(uuid4())

        return CancelTaskResponse(
            **await self._send_request(
                request.model_dump(mode='json', exclude_none=True),
                http_kwargs,
            )
        )

    async def set_task_callback(
        self,
        request: SetTaskPushNotificationConfigRequest,
        *,
        http_kwargs: dict[str, Any] | None = None,
    ) -> SetTaskPushNotificationConfigResponse:
        if not request.id:
            request.id = str(uuid4())

        return SetTaskPushNotificationConfigResponse(
            **await self._send_request(
                request.model_dump(mode='json', exclude_none=True),
                http_kwargs,
            )
        )

    async def get_task_callback(
        self,
        request: GetTaskPushNotificationConfigRequest,
        *,
        http_kwargs: dict[str, Any] | None = None,
    ) -> GetTaskPushNotificationConfigResponse:
        if not request.id:
            request.id = str(uuid4())

        return GetTaskPushNotificationConfigResponse(
            **await self._send_request(
                request.model_dump(mode='json', exclude_none=True),
                http_kwargs,
            )
        )
