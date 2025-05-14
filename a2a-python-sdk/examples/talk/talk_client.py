from a2a.client import A2AClient
from typing import Any
import httpx
from uuid import uuid4
from a2a.types import SendMessageSuccessResponse, Task
import asyncio

def print_welcome_message() -> None:
    print("欢迎使用A2A客户端！")
    print("请输入您的查询（输入 'exit' 退出）：")

def get_user_query() -> str:
    return input("\n> ")

async def interact_with_server(client: A2AClient) -> None:
    while True:
        user_input = get_user_query()
        if user_input.lower() == 'exit':
            print("再见！")
            break

        send_message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [
                    {'type': 'text', 'text': user_input}
                ],
                'messageId': uuid4().hex,
            },
        }

        try:
            response = await client.send_message(payload=send_message_payload)
            print(response.model_dump(mode='json', exclude_none=True))

            # stream_response = client.send_message_streaming(
            #     payload=send_message_payload
            # )
            # async for chunk in stream_response:
            #     print(chunk.model_dump(mode='json', exclude_none=True))

        except Exception as e:
            print(f"发生错误: {e}")

async def main() -> None:
    print_welcome_message()
    async with httpx.AsyncClient() as httpx_client:
        client = await A2AClient.get_client_from_agent_card_url(
            httpx_client, 'http://localhost:9999'
        )
        await interact_with_server(client)

if __name__ == '__main__':
    asyncio.run(main())