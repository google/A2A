import base64
import json
import logging
import os
import random
import string
import traceback
import urllib

import click
from agent import Magic8BallAgent
from agents.google_adk.task_manager import AgentTaskManager
from common.server import A2AServer
from common.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    AuthorizationCodeOAuthFlow,
    MissingAPIKeyError,
    OAuth2SecurityScheme,
    OAuthFlows,
)
from dotenv import load_dotenv
from middleware import get_oauth_flow, get_user_info_for_access_token, sign_in_with_google_oauth, GoogleOAuthMiddleware
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

# Web application route handlers standalone demonstrations

async def login(request: Request):
    flow = get_oauth_flow(request)
    authorization_url, state = flow.authorization_url(
        prompt='consent', access_type='offline', include_granted_scopes='true'
    )
    request.session['state'] = state
    return RedirectResponse(authorization_url)


async def logout(request: Request):
    request.session.clear()
    return RedirectResponse('/whoami')


async def whoami(request: Request):
    """Renders a "Whoami" page when logged in, or a sign-in page otherwise."""
    if 'user_info' not in request.session:
        return HTMLResponse("""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Agent Authentication with A2A and Google</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <!-- Materialize CSS -->
  <link href="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/css/materialize.min.css" rel="stylesheet">
  <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">

  <style>
    body {
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      margin: 0;
      background: linear-gradient(135deg, #e0f2f1, #ffffff);
      font-family: 'Roboto', sans-serif;
    }

    .card-panel {
      max-width: 500px;
      width: 90%;
      padding: 3rem 3rem 2.5rem;
      text-align: center;
      border-radius: 12px;
      box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
    }

    .brand-logo {
      font-size: 2rem;
      font-weight: 600;
      color: #2e7d32;
      margin-bottom: 1rem;
    }

    p.description {
      color: #555;
      margin: 1.5rem 0 2rem;
      font-size: 1.1rem;
      line-height: 1.6;
    }

    .google-btn {
      background-color: white;
      color: #444;
      border: 1px solid #ddd;
      font-weight: 500;
      text-transform: none;
      display: inline-flex;
      align-items: center;
      padding: 0.6rem 1.2rem;
      border-radius: 4px;
      font-size: 1rem;
      transition: background-color 0.2s;
    }

    .google-btn:hover {
      background-color: #f5f5f5;
    }

    .google-btn img {
      height: 20px;
      margin-right: 10px;
    }
  </style>
</head>
<body>

  <div class="card-panel z-depth-2">
    <h5>Agent Authentication with A2A and Google</h5>
    <p class="description">
      This is a sidecar application that is deployed alongside your A2AServer.
      You can use this application to <i>"Sign in with Google"</i>, authorize
      the test Google OAuth Client and get a Bearer Token so that you can make
      authenticated API calls to the A2AServer API.
    </p>

    <a href="/login" class="google-btn">
      <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google logo">
      Sign in with Google
    </a>
  </div>

  <!-- Materialize JS -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/js/materialize.min.js"></script>
</body>
</html>
""")

    user_info = request.session['user_info']
    user_token = request.session['user_token']

    return HTMLResponse(f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>User Profile</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <!-- Materialize CSS -->
  <link href="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/css/materialize.min.css" rel="stylesheet">

  <style>
    body {{
      background-color: #f5f5f5;
    }}
    .center-content {{
      display: flex;
      flex-direction: column;
      align-items: center;
    }}
    .code {{
      font-family: monospace;
      color: #222;
      white-space: pre-wrap;
      word-break: break-word;
      text-align: center;
      max-width: 100%;
    }}
    .info-label {{
      font-weight: bold;
      margin-top: 1rem;
      color: #555;
    }}
    .info-value {{
      margin-bottom: 1rem;
      color: #222;
    }}
    .logout-button {{
      position: absolute;
      top: 20px;
      right: 20px;
    }}
    .profile-card {{
      margin-top: 5vh;
    }}
    .profile-image {{
      width: 120px;
      height: 120px;
      object-fit: cover;
      border-radius: 50%;
      margin-bottom: 1rem;
    }}
  </style>
</head>
<body>

  <!-- Logout button -->
  <div class="logout-button">
    <a href="/logout" class="btn red darken-1">Logout</a>
  </div>

  <div class="container">
    <div class="row">
      <div class="col s12 m8 offset-m2 l6 offset-l3">
        <div class="card profile-card z-depth-2">
          <div class="card-content center-content">
            <img src="{user_info['picture']}" alt="Profile Picture" class="profile-image" crossorigin="credentials">

            <div class="info-label">Full Name</div>
            <div class="info-value">{user_info['name']}</div>

            <div class="info-label">Email Address</div>
            <div class="info-value">{user_info['email']}</div>

            <div class="info-label">Bearer Token</div>
            <div class="info-value code"><code>{user_token}</code></div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Materialize JS -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/js/materialize.min.js"></script>
</body>
</html>
''')


async def auth_handler(request: Request):
    try:
        credentials = await sign_in_with_google_oauth(request)
        state = request.query_params.get('state')
        oauth_callback = None

        try:
          oc_json = base64.b64decode(state).decode('utf-8')
          oauth_callback = json.loads(oc_json)
        except Exception:
            # This is not an OAUTH_CALLBACK header payload
            pass

        # Use OAUTH Callback redirect
        if oauth_callback:
            state_json = {
                'credentials': {
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_uri': credentials.token_uri,
                    'client_id': credentials.client_id,
                    'client_secret': credentials.client_secret,
                    'scopes': credentials.scopes,
                },
                'params': oauth_callback['params'],
            }
            query = {
                'state': base64.b64encode(json.dumps(state_json).encode('utf-8')).decode('utf-8'),
            }
            query_string = urllib.parse.urlencode({
                k: json.dumps(v) if isinstance(v, (dict, list)) else v
                for k, v in query.items()
            })

            return RedirectResponse(f'{oauth_callback["redirect_uri"]}?{query_string}')

        # Use standalone redirect
        token = credentials.token

        request.session['user_info'] = await get_user_info_for_access_token(token)
        request.session['user_token'] = token
        request.session['user_token_type'] = 'oauth2'

        return RedirectResponse('/whoami')
    except Exception as e:
        traceback.print_exc()
        return HTMLResponse(f"""<html>
  <body>
    <p>
      <b>Error:</b> {e}
    </p>
  </body>
</html>""")


@click.command()
@click.option('--host', default='localhost')
@click.option('--port', default=10002)
def main(host, port):
    """Spins up two A2AServers to demonstrate agent-level authentication."""
    if not os.getenv('GOOGLE_API_KEY'):
        raise MissingAPIKeyError('GOOGLE_API_KEY environment variable not set.')

    capabilities = AgentCapabilities(streaming=True)
    agent_card = AgentCard(
        name='Magic 8-Ball Agent',
        description='You are an agent that will answer questions as if you were a Magic 8-Ball.',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        defaultInputModes=Magic8BallAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=Magic8BallAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        securitySchemes={
            'google_oauth_client_app': OAuth2SecurityScheme(
                description=(
                    'Uses a Google OAuth client application that you sign in, authorize and get an access token'
                ),
                flows=OAuthFlows(
                    authorizationCode=AuthorizationCodeOAuthFlow(
                        authorizationUrl=GOOGLE_OAUTH_AUTH_URL,
                        tokenUrl=GOOGLE_OAUTH_TOKEN_URL,
                        scopes={
                            'openid': 'Associate you with your personal info on Google',
                            'https://www.googleapis.com/auth/userinfo.email': (
                                'See your primary Google Account email address'
                            ),
                            'https://www.googleapis.com/auth/userinfo.profile': (
                                "See your personal info, including any personal info you've made publicly available"
                            ),
                        },
                    ),
                ),
            ),
        },
        # Require either HTTP Authentication (ID Token provided by Google via "Sign in with Google") or OAuth2
        # (OAuth2 Access Token provided via "Sign in with Google" and authorizing the configured Google OAuth Client
        # Application).
        security=[
            {
                'google_oauth_client_app': [
                    'openid',
                    'https://www.googleapis.com/auth/userinfo.email',
                    'https://www.googleapis.com/auth/userinfo.profile',
                ],
            },
        ],
        skills=[
            AgentSkill(
                id='magic_8ball',
                name='Magic 8-Ball',
                description='Answers questions as if you were a Magic 8-Ball.',
                tags=['fun', 'magic-8ball'],
            ),
        ],
    )

    a2a_task_manager=AgentTaskManager(agent=Magic8BallAgent())
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
          # OAuth callback does not require an OAuth access token
          '/auth',
          # Web application endpoints do not require an OAuth access token (use application state)
          '/login',
          '/logout',
          '/whoami',
    ]

    # Web application paths DO NOT require authentication
    public_paths.extend(['/login', '/logout', '/whoami'])

    # OAuth callback route
    a2a_server.app.add_route('/auth', auth_handler)

    # Web application routes
    a2a_server.app.add_route('/login', login)
    a2a_server.app.add_route('/logout', logout)
    a2a_server.app.add_route('/whoami', whoami)

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
