import json
import logging
import os
import random
import string
import traceback

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
from middleware import sign_in_with_google_oauth, GoogleOAuthMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse

load_dotenv()

logging.basicConfig(level=logging.INFO)

CHARACTERS = string.ascii_letters + string.digits  # a-zA-Z0-9
CLIENT_ID = os.environ['GOOGLE_CLIENT_ID']
CLIENT_SECRET = os.environ['GOOGLE_CLIENT_SECRET']
GOOGLE_OAUTH_AUTH_URL = 'https://accounts.google.com/o/oauth2/auth'
GOOGLE_OAUTH_TOKEN_URL = 'https://oauth2.googleapis.com/token'
LOGGER = logging.getLogger(__name__)
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]
SECRET_KEY = ''.join(random.choices(CHARACTERS, k=32))


# OAuth handler
def make_oauth_handler(task_manager: AgentTaskManager):
    async def auth_handler(request: Request):
        try:
            credentials = await sign_in_with_google_oauth(request)

            # Update the credentials stored in the agent, and try again
            a2a_response = await task_manager.agent.update_credentials(
                request.query_params.get('state'),
                {
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_uri': credentials.token_uri,
                    'client_id': credentials.client_id,
                    'client_secret': credentials.client_secret,
                    'scopes': credentials.scopes,
                }
            )

            request.session['a2a_response'] = a2a_response.model_dump(exclude_none=True)

            return RedirectResponse('/result')
        except Exception as e:
            traceback.print_exc()
            return HTMLResponse(f"""<html>
      <body>
        <p>
          <b>Error:</b> {e}
        </p>
      </body>
    </html>""")

    return auth_handler

async def result(request: Request):
    if 'a2a_response' not in request.session:
        return HTMLResponse('''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Error</title>
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
  <style>
    body {
      margin: 0;
      font-family: 'Roboto', sans-serif;
      background-color: #fef2f2;
      color: #b91c1c;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100vh;
    }
    .container {
      max-width: 600px;
      text-align: center;
      background: #fff1f2;
      padding: 2rem 3rem;
      border-radius: 0.5rem;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    h1 {
      font-size: 2rem;
      margin-bottom: 0.5rem;
    }
    p {
      font-size: 1rem;
      margin-bottom: 1rem;
    }
    .code-box {
      background-color: #fef2f2;
      border: 1px solid #fca5a5;
      padding: 1rem;
      border-radius: 0.25rem;
      font-family: monospace;
      font-size: 0.9rem;
      color: #7f1d1d;
      overflow-x: auto;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Invalid Request</h1>
    <p>This endpoint should <b>ONLY</b> be used as a result of an OAuth redirect.</p>
  </div>
</body>
</html>''')

    response_json = json.dumps(request.session['a2a_response'], indent=2)

    return HTMLResponse(f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>API Landing Page</title>
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
    <div class="title">Authenticated Retry Result</div>
    <div class="card">
      <div class="sub-title">API Response</div>
      <pre class="preformatted">{response_json}</pre>
    </div>
  </div>
</body>
</html>''')


@click.command()
@click.option('--host', default='localhost')
@click.option(
    '--magic-8ball-url',
    help='The full URL to the Magic 8-Ball A2AServer (only applicable for personal-assistant agent)'
)
@click.option('--port', default=10003)
def main(host, magic_8ball_url, port):
    """Spins up two A2AServers to demonstrate agent-level authentication."""
    if not os.getenv('GOOGLE_API_KEY'):
        raise MissingAPIKeyError('GOOGLE_API_KEY environment variable not set.')

    capabilities = AgentCapabilities(streaming=True)
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

    a2a_task_manager=AgentTaskManager(agent=PersonalAssistantAgent())
    a2a_server = A2AServer(
        agent_card=agent_card,
        task_manager=a2a_task_manager,
        host=host,
        port=port,
    )

    # The public paths (those not authenticated by the GoogleOAuthMiddleware)
    public_paths = [
          # Agent card is publicly available (for now)
          '/.well-known/agent.json',
          # OAuth callback should be public
          '/auth',
          # Web application endpoints do not require an OAuth access token (use application state)
          '/result',
    ]

    # OAuth callback route
    a2a_server.app.add_route('/auth', make_oauth_handler(
        task_manager=a2a_task_manager,
    ))
    a2a_server.app.add_route('/result', result)

    # Configure the session middlewares
    a2a_server.app.add_middleware(SessionMiddleware, secret_key=''.join(random.choices(CHARACTERS, k=32)))
    a2a_server.app.add_middleware(
        GoogleOAuthMiddleware,
        agent_card=agent_card,
        public_paths=public_paths,
    )

    # Store the OAuth redirect URI
    a2a_server.app.state.oauth_redirect_uri = f'http://{host}:{port}/auth'

    a2a_server.start()


if __name__ == '__main__':
    main()
