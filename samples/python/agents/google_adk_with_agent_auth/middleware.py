import base64
import googleapiclient.discovery
import logging
import os
import sys

from agents.google_adk.task_manager import AgentTaskManager
from common.types import (
    OAuth2SecurityScheme,
)
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials

load_dotenv()

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

# Web application route handlers (and related)
def get_oauth_flow(request: Request):
    return Flow.from_client_config(
        client_config={
            'web': {
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'auth_uri': GOOGLE_OAUTH_AUTH_URL,
                'token_uri': GOOGLE_OAUTH_TOKEN_URL,
            }
        },
        scopes=SCOPES,
        redirect_uri=request.app.state.oauth_redirect_uri,
    )


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
    flow = get_oauth_flow(request)

    # Restore the previously saved state
    flow.state = request.session.get('state')

    flow.fetch_token(authorization_response=str(request.url))

    # Verify the OAuth2 state
    if request.session.get('state') != flow.state:
        raise Exception('OAuth Error (state mismatch)')

    return flow.credentials

# Starlette middleware for Google-based authentication
class GoogleOAuthMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that authenticates A2A access using a Google-provided Bearer Token."""

    def __init__(self, app, agent_card, public_paths):
        super().__init__(app)
        self.agent_card = agent_card
        self.public_paths = set(public_paths or [])

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
                    LOGGER.error(f'Security Scheme {name} of type oauth2 is missing authorizationCode flow')
                    sys.exit(1)

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
            return self._send_json_error(401, 'unauthorized', 'Missing or malformed Authorization header.', request)

        token = auth_header.split('Bearer ')[1]

        try:
            if self.a2a_auth:
                await get_user_info_for_access_token(token)
        except Exception as e:
            return self._send_json_error(403, 'forbidden', f'Authentication failed: {e}', request)

        return await call_next(request)

    def _send_json_error(self, status_code: int, error: str, reason: str, request: Request):
        flow = get_oauth_flow(request)
        oauth_callback = request.headers.get('OAUTH_CALLBACK')
        authorization_url, state = flow.authorization_url(
            prompt='consent', access_type='offline', include_granted_scopes='true',
            state=base64.b64encode(oauth_callback.encode('utf-8')).decode('utf-8') if oauth_callback else None,
        )
        return JSONResponse(
            {
                'error': error,
                'reason': reason,
                'hint': f'The Magic 8-Ball Agent requires authentication: {authorization_url}',
                'auth_url': authorization_url,
                'state': state,
            },
            status_code=status_code,
        )
