import base64
import json
import logging
import os
import traceback
import urllib

import click
from agent import PersonalAssistantAgent
from agents.google_adk.task_manager import AgentTaskManager
from common.server import A2AServer
from common.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    MissingAPIKeyError,
)
from dotenv import load_dotenv
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.types import Message

load_dotenv()

logging.basicConfig(level=logging.INFO)


async def oauth_callback(request: Request):
    try:
        state_json = base64.b64decode(request.query_params.get('state')).decode('utf-8')
        state = json.loads(state_json)
        params = state['params'] or {}
        parent_oauth_callback = params.get('parent_oauth_callback')

        # Update the credentials (demonstration purposes only)
        request.app.task_manager.agent.update_credentials(state['credentials'])

        if parent_oauth_callback:
            query = {
                'state': base64.b64encode(json.dumps(parent_oauth_callback).encode('utf-8')).decode('utf-8'),
            }
            query_string = urllib.parse.urlencode({
                k: json.dumps(v) if isinstance(v, (dict, list)) else v
                for k, v in query.items()
            })

            return RedirectResponse(f'{parent_oauth_callback['redirect_uri']}?{query_string}')
        else:
            return HTMLResponse(f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OAuth Callback</title>
  <style>
    body {{
      font-family: sans-serif;
      background-color: #f9fafb;
      padding: 2rem;
    }}
    .container {{
      max-width: 800px;
      margin: 0 auto;
    }}
    .card {{
      background: white;
      border-radius: 0.5rem;
      padding: 2rem;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }}
    .title {{
      font-size: 2rem;
      margin-bottom: 1rem;
    }}
    .sub-title {{
      font-size: 1.25rem;
      margin-bottom: 1rem;
    }}
    .preformatted {{
      background: #f3f4f6;
      padding: 1rem;
      border-radius: 0.25rem;
      overflow-x: auto;
      font-size: 0.9rem;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="title">Credentials Updated</div>
    <div class="card">
      <div class="sub-title">cURL Command to Retry</div>
      <pre class="preformatted">curl -X POST -d '{{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "message/send",
  "params": {{
    "id": "ms2",
    "configuration": {{
      "acceptedOutputModes": ["text"]
    }},
    "message": {{
      "contextId": "c1",
      "messageId": "m2",
      "role": "user",
      "parts": [
        {{
          "type": "text",
          "text": "Credentials have been provided to the agent, please retry."
        }}
      ],
      "taskId": "t1"
    }}
  }}
}}' http://localhost:10002/</pre>
    </div>
  </div>
</body>
</html>''')
    except Exception:
        traceback.print_exc()
        pass


class OAuthPassthroughMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Whenever the Demo UI calls a remote agent, the OAUTH_CALLBACK header is used to wire up the callback. We need
        # to pass this through.
        oc_header = request.headers.get('OAUTH_CALLBACK')

        if not oc_header:
            return await call_next(request)

        try:
            # Step 1: Read the body once
            body_bytes = await request.body()

            # Step 2: Parse the JSON
            original_data = json.loads(body_bytes)
            json_rpc_method = original_data.get('method')

            if json_rpc_method in ('message/send', 'message/stream'):
                params = original_data.get('params')
                message = params.get('message')
                metadata = message.get('metadata') or {}

                metadata['oauth_callback'] = json.loads(oc_header)

                message['metadata'] = metadata

            # Step 4: Serialize the modified JSON
            modified_body = json.dumps(original_data).encode("utf-8")

            # Step 3: Create a new receive() function
            async def receive() -> Message:
                return {"type": "http.request", "body": modified_body, "more_body": False}

            # Step 4: Build a new request with the modified body
            new_request = Request(request.scope, receive=receive)


            # Step 5: Pass modified request to next app handler
            return await call_next(new_request)
        except Exception:
            traceback.print_exc()
            # Fail gracefully: call_next with unmodified request
            return await call_next(request)


@click.command()
@click.option('--host', default='localhost')
@click.option(
    '--magic-8ball-url',
    help='The full URL to the Magic 8-Ball A2AServer (only applicable for personal-assistant agent)'
)
@click.option('--port', default=10002)
def main(host, magic_8ball_url, port):
    """Spins up two A2AServers to demonstrate agent-level authentication."""
    if not os.getenv('GOOGLE_API_KEY'):
        raise MissingAPIKeyError('GOOGLE_API_KEY environment variable not set.')

    capabilities = AgentCapabilities(streaming=False)
    agent_card = AgentCard(
        name='Personal Assistant Agent',
        description='This agent behaves as a personal assistant and is capable of answering all user questions.',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        defaultInputModes=PersonalAssistantAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=PersonalAssistantAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[
            AgentSkill(
                id='proxy_skill',
                name='Proxy',
                description='This agent behaves as a personal assistant and is capable of answering all user questions.',
                tags=['assistant', 'personal assistant', 'utility'],
            ),
        ],
    )

    if not magic_8ball_url:
        raise MissingAPIKeyError('--magic-8ball-url must be provided when running the Personal Assistant Agent')

    os.environ['MAGIC_8BALL_URL'] = magic_8ball_url
    os.environ['PERSONAL_ASSISTANT_URL'] = f'http://{host}:{port}'

    a2a_task_manager = AgentTaskManager(agent=PersonalAssistantAgent())
    a2a_server = A2AServer(
        agent_card=agent_card,
        task_manager=a2a_task_manager,
        host=host,
        port=port,
    )

    # Hack to provide the Task Manager to the OAuth callback
    a2a_server.app.task_manager = a2a_task_manager

    # OAuth callback route
    a2a_server.app.add_route('/oauth/callback', oauth_callback)

    a2a_server.app.add_middleware(
        OAuthPassthroughMiddleware,
    )

    a2a_server.start()


if __name__ == '__main__':
    main()
