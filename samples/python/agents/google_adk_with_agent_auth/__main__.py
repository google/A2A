import json
import logging
import os
import random
import string
import sys

import click
import googleapiclient.discovery

from agents.google_adk.task_manager import AgentTaskManager
from agent import Magic8BallAgent
from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, AuthorizationCodeOAuthFlow, MissingAPIKeyError, OAuth2SecurityScheme, OAuthFlows
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import id_token
from google.oauth2.credentials import Credentials
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request


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


# Demonstrate agent-level authentication/authorization via global (#/security) Security Requirements.
#
# See: https://swagger.io/specification/#security-requirement-object
#
# This demonstration configures an agent (via the AgentCard) to require authentication for all agent interactions. This
# demonstration is configured to require authentication using 'oauth2' Security Scheme, which will require the A2AServer
# API consumer to provide a Bearer Token (Access Token provided by Google OAuth Client application), and the Bearer
# Token will be verified, which in turn authenticates the user.
#
# Agent-level authentication/authorization is achieved by ensuring that Starlette requires
# authentication/authorization for all A2AServer API calls based on the sample Security Scheme and Security
# Requirements defined in the AgentCard. There is no attempt to do authentication/authorization for
# specific skills, tools or to provide authentication/authorization credentials to the agent impelmentation.
#
# For demononstration purposes only.


# Starlette middleware for Google-based authentication
class GoogleOAuthMiddleware(BaseHTTPMiddleware):
    '''Starlette middleware that authenticates A2A access using a Google-provided Bearer Token.'''
    def __init__(self, app, agent_card=None, public_paths=None):
        super().__init__(app)
        self.agent_card = agent_card
        self.public_paths = set(public_paths or [])

        # Process the AgentCard to identify what (if any) Security Requirements are defined at the root of the
        # AgentCard, indicating agent-level authentication/authorization.

        # Use app state for this demonstration (simplicity)
        self.a2a_auth = {}

        # Process the Security Requirements Object
        for sec_req in agent_card.security or []:
            # Since we pre-validated (non-exhaustive) the used parts of the Security Schemes and Security
            # Requirements, the code below WILL NOT do any validation.

            # An empty Security Requirement Object means you allow anonymous, no need to process any other Security
            # Requirements Objects
            if not sec_req:
                self.a2a_auth = {}
                break

            # Demonstrate how one could process the Security Requirements to configure the machinery used to
            # authenticate and/or authorize agent interactions.
            #
            # Note: This is written purely to support the sample and is for demonstration purposes only.
            for name, scopes in sec_req.items():
                sec_scheme = self.agent_card.securitySchemes[name]

                if isinstance(sec_scheme, OAuth2SecurityScheme):
                    self.a2a_auth = scopes

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Allow public paths and anonymous access
        if path in self.public_paths or not self.a2a_auth:
            return await call_next(request)

        # Authenticate the request
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return self._unauthorized('Missing or malformed Authorization header.', request)

        token = auth_header.split('Bearer ')[1]

        try:
            if self.a2a_auth:
                await get_user_info_for_access_token(token)
        except Exception as e:
            return self._forbidden(f'Authentication failed: {e}', request)

        return await call_next(request)

    def _forbidden(self, reason: str, request: Request):
        return JSONResponse(
            {
                'error': 'forbidden',
                'reason': reason,
                'hint': f'Get your Bearer Token via http://{request.url.hostname}:{request.url.port}/whoami',
            },
            status_code=403
        )

    def _unauthorized(self, reason: str, request: Request):
        return JSONResponse(
            {
                'error': 'unauthorized',
                'reason': reason,
                'hint': f'Get your Bearer Token via http://{request.url.hostname}:{request.url.port}/whoami',
            },
            status_code=401
        )


# OAuth handlers (and related)
async def auth(request: Request):
    try:
        return await sign_in_with_google_oauth(request)
    except Exception as e:
        return HTMLResponse(f'''<html>
  <body>
    <p>
      <b>Error:</b> {e}
    </p>
  </body>
</html>''')


async def get_user_info_for_access_token(token: str):
    # Wrap the token in a Credentials object
    credentials = Credentials(token=token)

    # You can force refresh if needed here
    if not credentials.valid and credentials.expired and credentials.refresh_token:
        credentials.refresh(GoogleAuthRequest())

    # Use the credentials to make a safe Google API call
    service = googleapiclient.discovery.build('oauth2', 'v2', credentials=credentials)

    return service.userinfo().get().execute()


async def sign_in_with_google_oauth(request: Request):
    flow = get_flow(request, SCOPES)

    # Restore the previously saved state
    flow.state = request.session.get('state')

    flow.fetch_token(authorization_response=str(request.url))

    # Verify the OAuth2 state
    if request.session.get('state') != flow.state:
        raise Exception('OAuth Error (state mismatch)')

    # Store credentials in session
    credentials = flow.credentials
    token = credentials.token

    request.session['user_info'] = await get_user_info_for_access_token(token)
    request.session['user_token'] = token
    request.session['user_token_type'] = 'oauth2'

    return RedirectResponse('/whoami')


# Web application route handlers (and related)
def get_flow(request: Request, scopes: list[str]):
    return Flow.from_client_config(
        client_config={
            'web': {
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'auth_uri': GOOGLE_OAUTH_AUTH_URL,
                'token_uri': GOOGLE_OAUTH_TOKEN_URL,
            }
        },
        scopes=scopes,
        redirect_uri=f'http://{request.url.hostname}:{request.url.port}/auth'
    )

async def login(request: Request):
    flow = get_flow(request, SCOPES)
    authorization_url, state = flow.authorization_url(
        prompt='consent',
        access_type='offline',
        include_granted_scopes='true')
    request.session['state'] = state
    return RedirectResponse(authorization_url)


async def logout(request: Request):
    request.session.clear()
    return RedirectResponse('/whoami')


async def whoami(request: Request):
    '''Renders a "Whoami" page when logged in, or a sign-in page otherwise.'''
    if 'user_info' not in request.session:
        return HTMLResponse('''<!DOCTYPE html>
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
''')

    user_info = request.session['user_info']
    user_token = request.session['user_token']
    user_token_type = request.session['user_token_type']

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


@click.command()
@click.option('--host', default='localhost')
@click.option('--port', default=10002)
def main(host, port):
    '''Spins up an A2AServer for the Magic 8-Ball agent.'''
    try:
        if not os.getenv('GOOGLE_API_KEY'):
                raise MissingAPIKeyError('GOOGLE_API_KEY environment variable not set.')

        capabilities = AgentCapabilities(streaming=True)
        skill = AgentSkill(
            id='magic_8ball',
            name='Magic 8-Ball Agent',
            description='Answers user questions as if you were a Magic 8-Ball.',
            tags=['fun', 'magic-8ball'],
        )
        agent_card = AgentCard(
            name='Magic 8-Ball Agent',
            description='You are an agent that will answer user questions as if you were a Magic 8-Ball.',
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
            skills=[skill],
        )
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=Magic8BallAgent()),
            host=host,
            port=port,
        )

        # Pre-validate the Security Schemes and Security Requirements (non-exhaustive, just simplifies middleware code)
        for index, sec_req in enumerate(agent_card.security or []):
            # Ensure that each security requirement is a dict
            if not isinstance(sec_req, dict):
                LOGGER.error(f'Security Requirement {index} is not an object')
                sys.exit(1)

            # Ensure that each referenced Security Scheme exists
            for name, scopes in sec_req.items():
                if name not in agent_card.securitySchemes:
                    LOGGER.error(f'Security Requirement {index} references missing Security Scheme {name}')
                    sys.exit(1)

                sec_scheme = agent_card.securitySchemes[name]

                if isinstance(sec_scheme, OAuth2SecurityScheme) and not sec_scheme.flows.authorizationCode:
                    LOGGER.error(
                        f'Security Scheme {name} of type oauth2 is missing authorizationCode flow'
                    )
                    sys.exit(1)

        # Configure the session middlewares
        server.app.add_middleware(SessionMiddleware, secret_key=''.join(random.choices(CHARACTERS, k=32)))
        server.app.add_middleware(GoogleOAuthMiddleware, agent_card=agent_card, public_paths=[
            # Agent card is publicly available (for now)
            '/.well-known/agent.json',
            # OAuth callback does not require an OAuth access token
            '/auth',
            # Web application endpoints do not require an OAuth access token (use application state)
            '/login',
            '/logout',
            '/whoami',
        ])

        # OAuth routes
        server.app.add_route('/auth', auth, methods=['GET', 'POST'])

        # Web application routes
        server.app.add_route('/login', login)
        server.app.add_route('/logout', logout)
        server.app.add_route('/whoami', whoami)

        server.start()
    except MissingAPIKeyError as e:
        LOGGER.error(f'Error: {e}')
        sys.exit(1)
    except Exception as e:
        LOGGER.error(f'An error occurred during server startup: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()
