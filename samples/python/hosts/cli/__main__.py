import asyncio
import base64
import os
import urllib

from uuid import uuid4

import asyncclick as click

from common.client import A2AClient, A2ACardResolver
from common.types import (
    TaskState,
    Task,
    Message,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
)
from common.utils.push_notification_auth import PushNotificationReceiverAuth


@click.command()
@click.option('--agent', default='http://localhost:10000')
@click.option('--session', default=0)
@click.option('--history', default=False)
@click.option('--use_push_notifications', default=False)
@click.option('--push_notification_receiver', default='http://localhost:5000')
async def cli(
    agent,
    session,
    history,
    use_push_notifications: bool,
    push_notification_receiver: str,
):
    card_resolver = A2ACardResolver(agent)
    card = card_resolver.get_agent_card()

    print('======= Agent Card ========')
    print(card.model_dump_json(exclude_none=True))

    notif_receiver_parsed = urllib.parse.urlparse(push_notification_receiver)
    notification_receiver_host = notif_receiver_parsed.hostname
    notification_receiver_port = notif_receiver_parsed.port

    if use_push_notifications:
        from hosts.cli.push_notification_listener import (
            PushNotificationListener,
        )

        notification_receiver_auth = PushNotificationReceiverAuth()
        await notification_receiver_auth.load_jwks(
            f'{agent}/.well-known/jwks.json'
        )

        push_notification_listener = PushNotificationListener(
            host=notification_receiver_host,
            port=notification_receiver_port,
            notification_receiver_auth=notification_receiver_auth,
        )
        push_notification_listener.start()

    client = A2AClient(agent_card=card)

    continue_loop = True
    streaming = card.capabilities.streaming

    while continue_loop:
        print('=========  starting a new task ======== ')
        continue_loop, contextId, taskId = await completeTask(
            client,
            streaming,
            use_push_notifications,
            notification_receiver_host,
            notification_receiver_port,
            None,
            None,
        )

        if history and continue_loop:
            print('========= history ======== ')
            task_response = await client.get_task(
                {'id': taskId, 'historyLength': 10}
            )
            print(
                task_response.model_dump_json(
                    include={'result': {'history': True}}
                )
            )


async def completeTask(
    client: A2AClient,
    streaming,
    use_push_notifications: bool,
    notification_receiver_host: str,
    notification_receiver_port: int,
    taskId,
    contextId,
):
    prompt = click.prompt(
        '\nWhat do you want to send to the agent? (:q or quit to exit)'
    )
    if prompt == ':q' or prompt == 'quit':
        return False, None, None

    message = {
        'role': 'user',
        'parts': [
            {
                'type': 'text',
                'text': prompt,
            }
        ],
        'messageId': str(uuid4()),
        'taskId': taskId,
        'contextId': contextId,
    }

    file_path = click.prompt(
        'Select a file path to attach? (press enter to skip)',
        default='',
        show_default=False,
    )
    if file_path and file_path.strip() != '':
        with open(file_path, 'rb') as f:
            file_content = base64.b64encode(f.read()).decode('utf-8')
            file_name = os.path.basename(file_path)

        message['parts'].append(
            {
                'type': 'file',
                'file': {
                    'name': file_name,
                    'bytes': file_content,
                },
            }
        )

    payload = {
        'id': str(uuid4()),
        'message': message,
        'configuration': {
            'acceptedOutputModes': ['text'],
        },
    }

    if use_push_notifications:
        payload['pushNotification'] = {
            'url': f'http://{notification_receiver_host}:{notification_receiver_port}/notify',
            'authentication': {
                'schemes': ['bearer'],
            },
        }

    taskResult = None
    message = None
    if streaming:
        response_stream = client.send_message_stream(payload)
        async for result in response_stream:
            if result.error:
                print(
                    f'\nError sending message {result.model_dump_json(exclude_none=True)}'
                )
                continue
            event = result.result
            if (
                isinstance(event, Task)
                or isinstance(event, TaskStatusUpdateEvent)
                or isinstance(event, TaskArtifactUpdateEvent)
            ):
                taskId = event.id
                contextId = event.contextId
            elif isinstance(event, Message):
                contextId = event.contextId
                message = event
            print(
                f'stream event => {result.model_dump_json(exclude_none=True)}'
            )
        # Upon completion of the stream. Retrieve the full task if one was made.
        if taskId:
            taskResult = await client.get_task({'id': taskId})
    else:
        # For non-streaming, assume the response is a task or message.
        result = await client.send_message(payload)
        if result.error:
            print(
                f'\nError sending message {result.model_dump_json(exclude_none=True)}'
            )
        if isinstance(result.result, Task):
            taskId = result.id
            contextId = result.contextId
            taskResult = result
        elif isinstance(result.result, Message):
            contextId = result.result.contextId
            message = result.result

    if message:
        print(f'\n{message.model_dump_json(exclude_none=True)}')
        return True, contextId, taskId
    if taskResult:
        print(f'\n{taskResult.model_dump_json(exclude_none=True)}')
        ## if the result is that more input is required, loop again.
        state = TaskState(taskResult.result.status.state)
        if state.name == TaskState.INPUT_REQUIRED.name:
            return (
                await completeTask(
                    client,
                    streaming,
                    use_push_notifications,
                    notification_receiver_host,
                    notification_receiver_port,
                    taskId,
                    contextId,
                ),
                contextId,
                taskId,
            )
        ## task is complete
        return True, contextId, taskId
    ## Failure case, shouldn't reach
    return True, contextId, taskId


if __name__ == '__main__':
    asyncio.run(cli())
