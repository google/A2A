import json
import os
from typing import Any
from a2a.types import AgentCard
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from auth0_api_python import ApiClient, ApiClientOptions


api_client = ApiClient(ApiClientOptions(
    domain=os.getenv('HR_AUTH0_DOMAIN'),
    audience=os.getenv('HR_AGENT_AUTH0_AUDIENCE'),
))


class OAuth2Middleware(BaseHTTPMiddleware):
    """Starlette middleware that authenticates A2A access using an OAuth2 bearer token."""
    def __init__(self, app: Starlette, agent_card: AgentCard = None, public_paths: list[str] = None):
        super().__init__(app)
        self.agent_card = agent_card
        self.public_paths = set(public_paths or [])

        # Process the AgentCard to identify what (if any) Security Requirements are defined at the root of the
        # AgentCard, indicating agent-level authentication/authorization.

        # Use app state for this demonstration (simplicity)
        self.a2a_auth = {}

        # Process the Authentication Requirements Object
        if agent_card.authentication:
            credentials = json.loads(agent_card.authentication.credentials or '{}')
            if 'scopes' in credentials:
                self.a2a_auth = { 'required_scopes': credentials['scopes'].keys() }

        # # Process the Security Requirements Object
        # for sec_req in agent_card.security or []:
        #     # Since we pre-validated (non-exhaustive) the used parts of the Security Schemes and Security
        #     # Requirements, the code below WILL NOT do any validation.

        #     # An empty Security Requirement Object means you allow anonymous, no need to process any other Security
        #     # Requirements Objects
        #     if not sec_req:
        #         break

        #     # Demonstrate how one could process the Security Requirements to configure the machinery used to
        #     # authenticate and/or authorize agent interactions.
        #     #
        #     # Note: This is written purely to support the sample and is for demonstration purposes only.
        #     for name, scopes in sec_req.items():
        #         # sec_scheme = self.agent_card.securitySchemes[name]

        #         # if not isinstance(sec_scheme, OAuth2SecurityScheme) or sec_scheme.flows.authorizationCode is None:
        #         #     raise NotImplementedError('Only OAuth2SecurityScheme -> ClientCredentialsOAuthFlow is supported.')

        #         self.a2a_auth = { 'required_scopes': scopes }

    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Allow public paths and anonymous access
        if path in self.public_paths or not self.a2a_auth:
            return await call_next(request)

        # Authenticate the request
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return self._unauthorized('Missing or malformed Authorization header.', request)

        access_token = auth_header.split('Bearer ')[1]

        try:
            if self.a2a_auth:
                payload = await api_client.verify_access_token(access_token=access_token)
                scopes = payload.get('scope', '').split()
                missing_scopes = [s for s in self.a2a_auth['required_scopes'] if s not in scopes]
                if missing_scopes:
                    return self._forbidden(f'Missing required scopes: {missing_scopes}', request)

        except Exception as e:
            return self._forbidden(f'Authentication failed: {e}', request)

        return await call_next(request)
    
    
    def _forbidden(self, reason: str, request: Request):
        accept_header = request.headers.get('accept', '')
        if 'text/event-stream' in accept_header:
            return PlainTextResponse(f'error forbidden: {reason}', status_code=403, media_type='text/event-stream')
        return JSONResponse({ 'error': 'forbidden', 'reason': reason }, status_code=403)

    
    def _unauthorized(self, reason: str, request: Request):
        accept_header = request.headers.get('accept', '')
        if 'text/event-stream' in accept_header:
            return PlainTextResponse(f'error unauthorized: {reason}', status_code=401, media_type='text/event-stream')
        return JSONResponse({ 'error': 'unauthorized', 'reason': reason }, status_code=401)
