import json

from collections.abc import AsyncIterable
from typing import Any

import httpx

from httpx._types import TimeoutTypes
from httpx_sse import connect_sse

from common.types import (
    A2AClientError,
    AgentCard,
    CancelTaskRequest,
    CancelTaskResponse,
    GetAuthenticatedExtendedCardRequest,
    GetAuthenticatedExtendedCardResponse,
    GetTaskPushNotificationRequest,
    GetTaskPushNotificationResponse,
    GetTaskRequest,
    GetTaskResponse,
    JSONRPCRequest,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageStreamRequest,
    SendMessageStreamResponse,
    SetTaskPushNotificationRequest,
    SetTaskPushNotificationResponse,
    httpx_error_to_a2a_error,
)


class A2AClient:
    def __init__(
        self,
        agent_card: AgentCard = None,
        url: str = None,
        timeout: TimeoutTypes = 60.0,
        default_headers: dict[str, str] | None = None,
    ):
        self.timeout = timeout
        if agent_card:
            self.url = agent_card.url
        elif url:
            self.url = url
        else:
            raise ValueError('Must provide either agent_card or url')
        self.default_headers = default_headers or {}

    async def send_message(self, payload: dict[str, Any]) -> SendMessageResponse:
        request = SendMessageRequest(params=payload)
        return SendMessageResponse(**await self._send_request(request))

    async def send_message_stream(self, payload: dict[str, Any]) -> AsyncIterable[SendMessageStreamResponse]:
        request = SendMessageStreamRequest(params=payload)
        headers = self.default_headers.copy()
        with httpx.Client(timeout=None) as client:
            with connect_sse(
                client, 'POST', self.url, json=request.model_dump(exclude_none=True), headers=headers
            ) as event_source:
                try:
                    for sse in event_source.iter_sse():
                        yield SendMessageStreamResponse(**json.loads(sse.data))
                except json.JSONDecodeError as e:
                    raise A2AClientError(str(e)) from e
                except httpx.HTTPError as e:
                    raise httpx_error_to_a2a_error(e, event_source)

    async def _send_request(
        self, request: JSONRPCRequest, extra_headers: dict[str, str] | None = None
    ) -> dict[str, Any]:
        headers = self.default_headers.copy()
        if extra_headers:
            headers.update(extra_headers)

        async with httpx.AsyncClient() as client:
            try:
                # Image generation could take time, adding timeout
                response = await client.post(
                    self.url, json=request.model_dump(exclude_none=True), timeout=self.timeout, headers=headers
                )
                response.raise_for_status()
                return response.json()
            except json.JSONDecodeError as e:
                raise A2AClientError(str(e)) from e
            except httpx.HTTPError as e:
                raise httpx_error_to_a2a_error(e)

    async def get_task(self, payload: dict[str, Any]) -> GetTaskResponse:
        request = GetTaskRequest(params=payload)
        return GetTaskResponse(**await self._send_request(request))

    async def cancel_task(self, payload: dict[str, Any]) -> CancelTaskResponse:
        request = CancelTaskRequest(params=payload)
        return CancelTaskResponse(**await self._send_request(request))

    async def set_task_callback(self, payload: dict[str, Any]) -> SetTaskPushNotificationResponse:
        request = SetTaskPushNotificationRequest(params=payload)
        return SetTaskPushNotificationResponse(**await self._send_request(request))

    async def get_task_callback(self, payload: dict[str, Any]) -> GetTaskPushNotificationResponse:
        request = GetTaskPushNotificationRequest(params=payload)
        return GetTaskPushNotificationResponse(**await self._send_request(request))

    async def get_authenticated_extended_card(
        self, auth_headers: dict[str, str] | None = None
    ) -> GetAuthenticatedExtendedCardResponse:
        request = GetAuthenticatedExtendedCardRequest()
        response_data = await self._send_request(request, extra_headers=auth_headers)
        return GetAuthenticatedExtendedCardResponse(**response_data)
