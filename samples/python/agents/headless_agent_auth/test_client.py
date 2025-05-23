import asyncio
import os

from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

import asyncclick as click
import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    GetTaskRequest,
    Message,
    MessageSendParams,
    OAuth2SecurityScheme,
    SendMessageRequest,
    SendStreamingMessageRequest,
    Task,
    TaskArtifactUpdateEvent,
    TaskQueryParams,
    TaskState,
    TaskStatusUpdateEvent,
    TextPart,
)
from auth0.authentication.get_token import GetToken
from dotenv import load_dotenv


load_dotenv()
access_token = None


class AgentAuth(httpx.Auth):
    """Custom httpx's authentication class to inject access token required by agent."""

    def __init__(self, agent_card: AgentCard):
        self.agent_card = agent_card

    def auth_flow(self, request):
        global access_token

        client_creds_flow = next(
            (
                scheme.root.flows.clientCredentials
                for scheme in self.agent_card.securitySchemes.values()
                if isinstance(scheme.root, OAuth2SecurityScheme)
                and scheme.root.flows.clientCredentials
            ),
            None,
        )
        if not client_creds_flow:
            yield request
            return

        if not access_token:
            token_url = client_creds_flow.tokenUrl
            print(f'\nFetching agent access token from {token_url}...')
            get_token = GetToken(
                domain=urlparse(token_url).hostname,
                client_id=os.getenv('A2A_CLIENT_AUTH0_CLIENT_ID'),
                client_secret=os.getenv('A2A_CLIENT_AUTH0_CLIENT_SECRET'),
            )
            access_token = get_token.client_credentials(
                os.getenv('HR_AGENT_AUTH0_AUDIENCE')
            )['access_token']
            print('Done.\n')

        request.headers['Authorization'] = f'Bearer {access_token}'
        yield request


@click.command()
@click.option('--agent', default='http://localhost:10050')
@click.option('--context_id')
@click.option('--history', default=False, is_flag=True)
@click.option('--debug', default=False, is_flag=True)
async def cli(agent: str, context_id: str | None, history: bool, debug: bool):
    async with httpx.AsyncClient() as httpx_client:
        agent_card = await A2ACardResolver(
            httpx_client=httpx_client,
            base_url=agent,
        ).get_agent_card()

        print('======= Agent Card ========')
        print(agent_card.model_dump_json(exclude_none=True, indent=2))

        httpx_client.auth = AgentAuth(agent_card)

        client = A2AClient(
            httpx_client=httpx_client,
            agent_card=agent_card,
        )

        if not context_id:
            context_id = uuid4().hex

        continue_loop = True
        streaming = agent_card.capabilities.streaming

        while continue_loop:
            task_id = uuid4().hex
            print('=========  Starting a New Task ======== ')
            continue_loop = await complete_task(
                client,
                streaming,
                task_id,
                context_id,
                debug,
            )

            if history and continue_loop:
                print('========= History ======== ')
                get_task_response = await client.get_task(
                    GetTaskRequest(
                        params=TaskQueryParams(id=task_id, historyLength=10)
                    )
                )
                print(
                    get_task_response.root.model_dump_json(
                        include={'result': {'history': True}}
                    )
                )


def create_send_params(
    text: str, task_id: str | None = None, context_id: str | None = None
) -> MessageSendParams:
    """Helper function to create the payload for sending a task."""
    send_params: dict[str, Any] = {
        'message': {
            'role': 'user',
            'parts': [{'kind': 'text', 'text': text}],
            'messageId': uuid4().hex,
        },
        'configuration': {
            'acceptedOutputModes': ['text'],
        },
    }

    if task_id:
        send_params['message']['taskId'] = task_id

    if context_id:
        send_params['message']['contextId'] = context_id

    return MessageSendParams(**send_params)


async def complete_task(
    client: A2AClient,
    streaming: bool,
    task_id: str,
    context_id: str,
    debug: bool = False,
) -> bool:
    prompt = click.prompt(
        '\nWhat do you want to send to the agent? (:q or quit to exit)'
    )

    if prompt == ':q' or prompt == 'quit':
        return False

    send_params = create_send_params(
        text=prompt,
        task_id=task_id,
        context_id=context_id,
    )

    task = None
    if streaming:
        stream_response = client.send_message_streaming(
            SendStreamingMessageRequest(params=send_params)
        )
        async for chunk in stream_response:
            result = chunk.root.result
            print(
                f'stream event => {chunk.root.model_dump_json(exclude_none=True)}'
                if debug
                else (
                    next(
                        (
                            f'stream message => role: {result.role.value}, kind:'
                            f' {part.root.kind}, text: {part.root.text}'
                            for part in result.parts
                            if isinstance(part.root, TextPart)
                        ),
                        '',
                    )
                    if isinstance(result, Message)
                    else next(
                        (
                            f'stream message => role: {msg.role.value}, kind:'
                            f' {part.root.kind}, text: {part.root.text}'
                            for msg in result.history or []
                            for part in msg.parts
                            if isinstance(part.root, TextPart)
                        ),
                        '',
                    )
                    if isinstance(result, Task)
                    else next(
                        (
                            'stream message => role:'
                            f' {result.status.message.role.value}, kind:'
                            f' {part.root.kind}, text: {part.root.text}'
                            for part in (
                                result.status.message.parts
                                if result.status.message
                                else []
                            )
                            if isinstance(part.root, TextPart)
                        ),
                        '',
                    )
                    if isinstance(result, TaskStatusUpdateEvent)
                    else next(
                        (
                            f'stream artifact => kind: {part.root.kind}, text:'
                            f' {part.root.text}'
                            for part in result.artifact.parts
                            if isinstance(part.root, TextPart)
                        ),
                        '',
                    )
                    if isinstance(result, TaskArtifactUpdateEvent)
                    else ''
                )
            )

        get_task_response = await client.get_task(
            GetTaskRequest(params=TaskQueryParams(id=task_id))
        )
        task = get_task_response.root.result
    else:
        send_message_response = await client.send_message(
            SendMessageRequest(params=send_params)
        )
        task = send_message_response.root.result
        print(f'\n{task.model_dump_json(exclude_none=True)}')

    # if the result is that more input is required, loop again.
    if task.status.state == TaskState.input_required:
        return await complete_task(
            client,
            streaming,
            task_id,
            context_id,
            debug,
        )

    # task is complete
    return True


if __name__ == '__main__':
    asyncio.run(cli())
