import os
from fastapi import Depends, FastAPI
from fastapi_plugin import Auth0FastAPI

auth0 = Auth0FastAPI(
    domain=os.getenv('HR_AUTH0_DOMAIN'),
    audience=os.getenv('HR_API_AUTH0_AUDIENCE'),
)

app = FastAPI()

@app.get('/employees/{id}')
def get_employee(
    id: str,
    _claims: dict = Depends(auth0.require_auth(scopes='read:employee'))
):
    # TODO: if needed, return more employee details
    return {'employee_id': id}

hr_api = app
