from a2a.client import A2AClient
from typing import Any
import httpx
from uuid import uuid4
from a2a.types import SendMessageSuccessResponse, Task


async def main() -> None:
    async with httpx.AsyncClient() as httpx_client:
        client = await A2AClient.get_client_from_agent_card_url(
            httpx_client, 'http://localhost:9999'
        )
        send_message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [
                    {'type': 'text', 'text': 'how much is 10 USD in INR?'}
                ],
                'messageId': uuid4().hex,
            },
        }

        response = await client.send_message(payload=send_message_payload)
        print(response.model_dump(mode='json', exclude_none=True))

        if isinstance(response.root, SendMessageSuccessResponse) and isinstance(
            response.root.result, Task
        ):
            task_id: str = response.root.result.id
            get_task_payload = {'id': task_id}
            get_response = await client.get_task(payload=get_task_payload)
            print(get_response.model_dump(mode='json', exclude_none=True))

            cancel_task_payload = {'id': task_id}
            cancel_response = await client.cancel_task(
                payload=cancel_task_payload
            )
            print(cancel_response.model_dump(mode='json', exclude_none=True))
        else:
            print(
                'Received an instance of Message, getTask and cancelTask are not applicable for invocation'
            )

        stream_response = client.send_message_streaming(
            payload=send_message_payload
        )
        async for chunk in stream_response:
            print(chunk.model_dump(mode='json', exclude_none=True))


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
