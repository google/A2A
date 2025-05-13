# Agent-level Authentication/Authorization via Google ADK and Google OAuth

This sample uses the Agent Development Kit (ADK) to create a simple agent that uses uses A2A and Google OAuth to secure
access to your agent.

**Note:** This is a WIP _(Work in Progress)_

## Prerequisites

- Python 3.12 or higher
- [UV](https://docs.astral.sh/uv/)
- Access to an LLM and API Key
- Access to a [Google OAuth Application](https://developers.google.com/identity/protocols/oauth2)

## Scenarios

All scenarios in this sample have an ADK Agent sitting behind an `A2AServer`, but the `A2AServer` has been extended to
have an OAuth callback handler, as well as a simple Web UI for signing in with Google and authorizing your OAuth Client
application _(to get your Bearer Token)_. No modifications were made to the `A2AServer` API/handlers, the extensions
were made directly to the HTTP Server that the `A2AServer` builds upon _(Starlette: [https://www.starlette.io/])_.

To enforce authentication of the `A2AServer`, a sample Starlette middleware was created that wires up authentication
based on the global _(`#/security`) Security Requirements_ in the `AgentCard`.

### Direct Authentication

Direct Authentication is some application, user or agent needing to provide authentication credentials to the agent's
`A2AServer` directly. _(`U -> A [auth required]`)_ Exactly how this would work in the real-world depends on your agentic
environment. For this sample, we will pretend to be an `A2AClient` by making pure cURL requests to the Magic 8-Ball
Agent.

#### Running the Sample

1. Navigate to the samples directory:

    ```bash
    cd samples/python/agents/google_adk_with_agent_authn
    ```

2. Create an environment file and update with the appropriate environment variables:

   ```bash
   cp .env.example .env
   ```

3. Run the agent:

    ```bash
    uv run magic_8ball.py
    ```

4. Interact with the agent:

    - `curl`

        - Make the unauthenticated call

        ```text
        curl -X POST -d '{
          "jsonrpc": "2.0",
          "id": 1,
          "method": "message/send",
          "params": {
            "id": "t1",
            "sessionId": "fa09c65ea23a4ee59f9f2017ea01183a",
            "configuration": {
              "acceptedOutputModes": ["text"]
            },
            "message": {
              "messageId": "m1",
              "role": "user",
              "parts": [
                {
                  "type": "text",
                  "text": "Consult the magic 8-ball and ask the following: Will the Braves win the World Series?"
                }
              ]
            }
          }
        }' http://localhost:10002/ | jq .
        ```

        You should get an authorization error back that looks like this:

        ```json
        {
          "error": "unauthorized",
          "reason": "Missing or malformed Authorization header.",
          "hint": "The Magic 8-Ball Agent requires authentication: {OAUTH_AUTH_URL}",
          "auth_url": "{OAUTH_AUTH_URL}",
          "state": "{OAUTH_STATE_VARIABLE}"
        }
        ```

        - Visit the URL in `auth_url` so you can get your access token by signing in with Google and authorizing your
        OAuth application, and returning you to [http://localhost:10002/whoami] which renders a page with profile
        details and the Bearer Token you will use in the subsequent `A2AServer` call

        - Make the authenticated call

        ```text
        curl -X POST -d '{
          "jsonrpc": "2.0",
          "id": 1,
          "method": "message/send",
          "params": {
            "id": "t1",
            "sessionId": "fa09c65ea23a4ee59f9f2017ea01183a",
            "configuration": {
              "acceptedOutputModes": ["text"]
            },
            "message": {
              "messageId": "m1",
              "role": "user",
              "parts": [
                {
                  "type": "text",
                  "text": "Consult the magic 8-ball and ask the following: Will the Braves win the World Series?"
                }
              ]
            }
          }
        }' -H 'Authorization: Bearer {BEARER_TOKEN}' http://localhost:10002/ | jq .
        ```

        You should get a response back that looks like this:

        ```json
        {
          "jsonrpc": "2.0",
          "id": 1,
          "result": {
            "id": "f4ae08ba-7337-4f3b-ab95-b205b049dbcc",
            "contextId": "13e3a554-8761-49a7-ab03-a8e3790bef91",
            "status": {
              "state": "completed",
              "timestamp": "2025-05-13T14:47:09.999442"
            },
            "artifacts": [
              {
                "parts": [
                  {
                    "type": "text",
                    "text": "Very doubtful\n"
                  }
                ],
                "index": 0
              }
            ],
            "history": [
              {
                "role": "user",
                "parts": [
                  {
                    "type": "text",
                    "text": "Consult the magic 8-ball and ask the following: Will the Braves win the World Series?"
                  }
                ],
                "messageId": "m1",
                "contextId": "13e3a554-8761-49a7-ab03-a8e3790bef91",
                "taskId": "f4ae08ba-7337-4f3b-ab95-b205b049dbcc"
              }
            ]
          }
        }
        ```

    - `A2AClient` _(TBD, waiting on the SDK to firm up)_
    - Demo CLI _(TBD, waiting no the SDK to firm up)_
    - Demo UI _(TBD, updating the Demo UI in another PR)_

### Nested Authentication

Nested Authentication is some application, user or agent interacting with another agent, that itself needs to provide
authentication credentials to another agent's `A2AServer`. _(`U -> A -> B [auth required]`)_ Exactly how this would work
in the real-world depends on your agentic environment. For this sample, we will spin up a Personal Assistant Agent that
uses an `A2AClient` to make requests to the Magic 8-Ball Agent.

#### Running the Sample

1. Navigate to the samples directory:

    ```bash
    cd samples/python/agents/google_adk_with_agent_authn
    ```

2. Create an environment file and update with the appropriate environment variables:

   ```bash
   cp .env.example .env
   ```

3. Run the Magic 8-Ball agent:

    ```bash
    uv run magic_8ball.py
    ```

5. Run the Personal Assistant agent _(`--magic-8ball-url` is required to tell where the Magic 8-Ball `A2AServer` is)_:

    ```bash
    uv run personal_assistant.py --magic-8ball-url={MAGIC_8BALL_URL}
    ```

4. Interact with the Personal Assistant Agent:

    - `curl`

        - Make the unauthenticated call

        ```text
        curl -X POST -d '{
          "jsonrpc": "2.0",
          "id": 1,
          "method": "message/send",
          "params": {
            "id": "t1",
            "sessionId": "fa09c65ea23a4ee59f9f2017ea01183a",
            "configuration": {
              "acceptedOutputModes": ["text"]
            },
            "message": {
              "messageId": "m1",
              "role": "user",
              "parts": [
                {
                  "type": "text",
                  "text": "Consult the magic 8-ball and ask the following: Will the Braves win the World Series?"
                }
              ]
            }
          }
        }' http://localhost:10003/ | jq .
        ```

        You should get an authorization error back that looks like this:

        ```json
        {
          "jsonrpc": "2.0",
          "id": 1,
          "result": {
            "id": "94408715-337a-440d-9ee2-af09ba7c6dcb",
            "contextId": "6ce2e6e4-ca5b-40a6-8738-424e221311fa",
            "status": {
              "state": "auth-required",
              "message": {
                "role": "agent",
                "parts": [
                  {
                    "type": "text",
                    "text": "Missing or malformed Authorization header."
                  }
                ],
                "messageId": "5c07791d-cefa-4f1d-8218-920378677b67",
                "contextId": "6ce2e6e4-ca5b-40a6-8738-424e221311fa",
                "taskId": "94408715-337a-440d-9ee2-af09ba7c6dcb",
                "metadata": {
                  "error": "unauthorized",
                  "reason": "Missing or malformed Authorization header.",
                  "hint": "The Magic 8-Ball Agent requires authentication: {OAUTH_AUTH_URL}",
                  "auth_url": "{OAUTH_AUTH_URL}",
                  "state": "{OAUTH_STATE_VARIABLE}",
                  "status_code": 401
                }
              },
              "timestamp": "2025-05-13T14:55:56.078589"
            },
            "artifacts": [],
            "history": [
              {
                "role": "user",
                "parts": [
                  {
                    "type": "text",
                    "text": "Consult the magic 8-ball and ask the following: Will the Braves win the World Series?"
                  }
                ],
                "messageId": "m1",
                "contextId": "6ce2e6e4-ca5b-40a6-8738-424e221311fa",
                "taskId": "94408715-337a-440d-9ee2-af09ba7c6dcb"
              }
            ]
          }
        }
        ```

        - Visit the URL in `auth_url` so you can get your access token by signing in with Google and authorizing your
        OAuth application, and returning you to [http://localhost:10003/result] which renders a page with the response
        of the continued `Task` after the OAuth handshake occured. Here is an example:

        ```json
        {
          "jsonrpc": "2.0",
          "id": "d81d21e9-6e06-4da5-ae0f-b80fdd10663d",
          "result": {
            "id": "c0ea029c-2f0a-43ba-b657-8cdc75d67ceb",
            "contextId": "80d16d28-d9ac-4fff-b93d-27fdf6a5bae5",
            "status": {
              "state": "completed",
              "timestamp": "2025-05-13T15:31:17.222597"
            },
            "artifacts": [
              {
                "parts": [
                  {
                    "type": "text",
                    "text": "My reply is no\n"
                  }
                ],
                "index": 0
              }
            ],
            "history": [
              {
                "role": "user",
                "parts": [
                  {
                    "type": "text",
                    "text": "Consult the magic 8-ball and ask the following: Will the Braves win the World Series?"
                  }
                ],
                "messageId": "m1",
                "contextId": "80d16d28-d9ac-4fff-b93d-27fdf6a5bae5",
                "taskId": "c0ea029c-2f0a-43ba-b657-8cdc75d67ceb"
              },
              {
                "role": "user",
                "parts": [
                  {
                    "type": "text",
                    "text": "Credentials have been provided to the agent, please retry."
                  }
                ],
                "messageId": "f029fb1c-5bf5-4efd-8737-633a60fa57e7",
                "contextId": "80d16d28-d9ac-4fff-b93d-27fdf6a5bae5",
                "taskId": "c0ea029c-2f0a-43ba-b657-8cdc75d67ceb"
              }
            ]
          }
        }
        ```

        - Subsequent requests should succeed without needing to re-authenticate until the token expires

    - Demo CLI _(TBD, waiting no the SDK to firm up)_
    - Demo UI _(TBD, updating the Demo UI in another PR)_
