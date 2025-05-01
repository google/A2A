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

**Note:** Streaming is **DISABLED** for this sample due to Personal Assistant Agent stream closing too early, which may
be _(not saying it as fact, just based discussions about OOB impacts on open streams)_ due to the A2A demonstration
machinery.

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

        - Make the unauthenticated cal

        ```text
        curl -X POST -d '{
          "jsonrpc": "2.0",
          "id": 1,
          "method": "message/send",
          "params": {
            "id": "ms1",
            "configuration": {
              "acceptedOutputModes": ["text"]
            },
            "message": {
              "contextId": "c1",
              "messageId": "m1",
              "role": "user",
              "parts": [
                {
                  "type": "text",
                  "text": "Consult the magic 8-ball and ask the following: Will the Braves win the World Series?"
                }
              ],
              "taskId": "t1"
            }
          }
        }' http://localhost:10002/
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
            "id": "ms1",
            "configuration": {
              "acceptedOutputModes": ["text"]
            },
            "message": {
              "contextId": "c1",
              "messageId": "m1",
              "role": "user",
              "parts": [
                {
                  "type": "text",
                  "text": "Consult the magic 8-ball and ask the following: Will the Braves win the World Series?"
                }
              ],
              "taskId": "t1"
            }
          }
        }' -H 'Authorization: Bearer {BEARER_TOKEN}' http://localhost:10002/
        ```

        You should get a response back that looks like this:

        ```json
        {
          "jsonrpc": "2.0",
          "id": 1,
          "result": {
            "id": "ms1",
            "contextId": "c1",
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
                "contextId": "c1",
                "taskId": "t1"
              }
            ]
          }
        }
        ```

    - Demo UI

        - Open the Demo UI _([http://0.0.0.0:12000])_

        - Register the Magic 8-Ball Agent using _(`localhost:10002`)_

        - Create a new conversation

        - Interact with the UI _(Example: `Consult the Magic 8-Ball and ask the following: Will the Braves win the World Series?`)_

        - Click the _Sign in with Google_ button

        - Login to Google, and authorize the OAuth Client application

        - You should be redirected to your conversation with the question already being answered

        - Any follow up questions will use persisted credentials until token expires

    - Demo CLI _(TBD)_

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
    uv run magic_8ball.py --port=10003
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
            "id": "ms1",
            "configuration": {
              "acceptedOutputModes": ["text"]
            },
            "message": {
              "contextId": "c1",
              "messageId": "m1",
              "role": "user",
              "parts": [
                {
                  "type": "text",
                  "text": "Consult the magic 8-ball and ask the following: Will the Braves win the World Series?"
                }
              ],
              "taskId": "t1"
            }
          }
        }' http://localhost:10002/
        ```

        You should get an authorization error back that looks like this:

        ```json
        {
          "jsonrpc": "2.0",
          "id": 1,
          "result": {
            "id": "t1",
            "contextId": "c1",
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
                "messageId": "585cc918-de68-4997-a909-1d0464c82454",
                "contextId": "c1",
                "taskId": "t1",
                "metadata": {
                  "error": "unauthorized",
                  "reason": "Missing or malformed Authorization header.",
                  "hint": "The Magic 8-Ball Agent requires authentication: {OAUTH_AUTHORIZATION_URL}",
                  "auth_url": "{OAUTH_AUTHORIZATION_URL}",
                  "state": "{OAUTH_STATE}",
                  "status_code": 401
                }
              },
              "timestamp": "2025-05-14T11:18:55.894264"
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
                "contextId": "c1",
                "taskId": "t1"
              }
            ]
          }
        }
        ```

        - Visit the URL in `auth_url` so you can get your access token by signing in with Google and authorizing your
        OAuth application, and returning you to [http://localhost:10002/oauth/callback] which renders an example `curl`
        command to retry the request now that credentials have been updated:

        ```text
        curl -X POST -d '{
          "jsonrpc": "2.0",
          "id": 2,
          "method": "message/send",
          "params": {
            "id": "ms2",
            "configuration": {
              "acceptedOutputModes": ["text"]
            },
            "message": {
              "contextId": "c1",
              "messageId": "m2",
              "role": "user",
              "parts": [
                {
                  "type": "text",
                  "text": "Credentials have been provided to the agent, please retry."
                }
              ],
              "taskId": "t1"
            }
          }
        }' http://localhost:10002/
        ```

        - You should get a response back like this:

        ```json
        {
          "jsonrpc": "2.0",
          "id": 2,
          "result": {
            "id": "t1",
            "contextId": "c1",
            "status": {
              "state": "completed",
              "timestamp": "2025-05-14T11:39:56.296317"
            },
            "artifacts": [
              {
                "parts": [
                  {
                    "type": "text",
                    "text": "Yes - definitely\n"
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
                "contextId": "c1",
                "taskId": "t1"
              },
              {
                "role": "user",
                "parts": [
                  {
                    "type": "text",
                    "text": "Credentials have been provided to the agent, please retry."
                  }
                ],
                "messageId": "m2",
                "contextId": "c1",
                "taskId": "t1"
              }
            ]
          }
        }
        ```

    - Demo UI

        - Open the Demo UI _([http://0.0.0.0:12000])_

        - Register the Personal Assistant Agent using _(`localhost:10002`)_

        - Create a new conversation

        - Interact with the UI _(Example: `Consult the Magic 8-Ball and ask the following: Will the Braves win the World Series?`)_

        - Click the _Sign in with Google_ button

        - Login to Google, and authorize the OAuth Client application

        - You should be redirected to your conversation with the question already being answered

        - Any follow up questions will use persisted credentials until token expires

    - Demo CLI _(TBD)_
