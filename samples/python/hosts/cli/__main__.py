import asyncclick as click
import asyncio
import base64
import os
import urllib
import json
from uuid import uuid4

from common.client import A2AClient, A2ACardResolver
from common.types import TaskState, Task, TextPart, FilePart, DataPart, Artifact
from common.utils.push_notification_auth import PushNotificationReceiverAuth
from common.utils.etl import truncate_leaves


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
    print(card.model_dump_json(exclude_none=True, indent=2))

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
    if session == 0:
        sessionId = uuid4().hex
    else:
        sessionId = session

    continue_loop = True
    streaming = card.capabilities.streaming

    while continue_loop:
        taskId = uuid4().hex
        print('=========  starting a new task ======== ')
        continue_loop = await completeTask(
            client,
            streaming,
            use_push_notifications,
            notification_receiver_host,
            notification_receiver_port,
            taskId,
            sessionId,
        )

        if history and continue_loop:
            print('========= history ======== ')
            task_response = await client.get_task(
                {'id': taskId, 'historyLength': 10}
            )
            print(
                task_response.model_dump_json(
                    include={'result': {'history': True}}, indent=2
                )
            )


def handle_artifact(artifact: Artifact) -> None:
    """
    Handle artifacts artifacts by part type.

    Currently it handles the files by part type: FilePart is saved to a file in CWD/tmp/, TextPart is printed to the console, DataPart is passed through, other types raise an error.

    Args:
        artifact (Artifact): The artifact to handle

    Returns:
        None

    Raises:
        ValueError: If the part type is not handled
    """
    try:
        for part in artifact.parts:
            if isinstance(part, FilePart):
                if not part.file.mimeType:
                    raise ValueError('Missing mime type for file')

                tmp_dir = os.path.join(os.getcwd(), 'tmp')
                os.makedirs(tmp_dir, exist_ok=True)
                file_name = part.file.name
                file_type = part.file.mimeType
                file_extension = file_type.split('/')[1]
                file_path = os.path.join(
                    tmp_dir, f'{file_name}.{file_extension}'
                )

                try:
                    with open(file_path, 'wb') as f:
                        # create bytes object from base64 encoded string
                        file_bytes = base64.b64decode(part.file.bytes)
                        f.write(file_bytes)
                    print(f'File saved to:\n{file_path}\n\n')
                except IOError as e:
                    print(f'Failed to write file {file_path}: {e}')

            elif isinstance(part, TextPart):
                print(f'Text content pass-through.')
            elif isinstance(part, DataPart):
                print(f'Data content pass-through.')
            else:
                raise ValueError(f'Unknown part type: {type(part)}')
    except Exception as e:
        print(f'Error handling artifact: {e}')
        raise


async def completeTask(
    client: A2AClient,
    streaming,
    use_push_notifications: bool,
    notification_receiver_host: str,
    notification_receiver_port: int,
    taskId,
    sessionId,
):
    prompt = click.prompt(
        '\nWhat do you want to send to the agent? (:q or quit to exit)'
    )
    if prompt == ':q' or prompt == 'quit':
        return False

    message = {
        'role': 'user',
        'parts': [
            {
                'type': 'text',
                'text': prompt,
            }
        ],
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
        'id': taskId,
        'sessionId': sessionId,
        'acceptedOutputModes': ['text'],
        'message': message,
    }

    if use_push_notifications:
        payload['pushNotification'] = {
            'url': f'http://{notification_receiver_host}:{notification_receiver_port}/notify',
            'authentication': {
                'schemes': ['bearer'],
            },
        }

    taskResult = None
    if streaming:
        response_stream = client.send_task_streaming(payload)
        async for result in response_stream:
            print(
                f'stream event => {result.model_dump_json(exclude_none=True)}'
            )
        taskResult = await client.get_task({'id': taskId})
    else:
        taskResult = await client.send_task(payload)

        taskResultTruncatedLeaves = truncate_leaves(taskResult.model_dump())

        print(f'========= Task results ========')
        print(json.dumps(taskResultTruncatedLeaves, indent=2))

        for artifact in taskResult.result.artifacts:
            handle_artifact(artifact)

    ## if the result is that more input is required, loop again.
    state = TaskState(taskResult.result.status.state)
    if state.name == TaskState.INPUT_REQUIRED.name:
        return await completeTask(
            client,
            streaming,
            use_push_notifications,
            notification_receiver_host,
            notification_receiver_port,
            taskId,
            sessionId,
        )
    else:
        ## task is complete
        return True


if __name__ == '__main__':
    asyncio.run(cli())
