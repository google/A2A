# Agent-level Authentication/Authorization via Google ADK and Google OAuth

This sample uses the Agent Development Kit (ADK) to create a simple agent that uses uses A2A and Google OAuth to secure
access to your agent.

**Note:** This is a WIP _(Work in Progress)_

## Prerequisites

- Python 3.12 or higher
- [UV](https://docs.astral.sh/uv/)
- Access to an LLM and API Key
- Access to a [Google OAuth Application](https://developers.google.com/identity/protocols/oauth2)

## Overview

To demonstrate agent-level authentication, we have created two separate agents:

1. **Personal Assistant Agent:** This agent answers any user requests, but is written to proxy through to the
  _Magic 8-Ball Agent_ any time a pertinent user question is received _(For example, any question that is vague/playful
  and can be answered with maybe/no/yes, or when the user explicitly asks an answer of the Magic 8-Ball, the Magic
  8-Ball Agent should be consulted.)_
2. **Magic 8-Ball Agent:** This agent will behave as a Magic 8-Ball

The _Personal Assistant Agent_ **DOES NOT** require any level of authentication, but the _Magic 8-Ball Agent_ **DOES**.
While designing this sample, we came up with two scenarios that showcase how agent-level authentication may be work:

1. **Direct Authentication:** _(`U -> A [auth required]`)_ This scenario is for any non-agent directly making requests
  to the _Magic 8-Ball Agent_, where the `A2AClient` itself needs to be configured by the controlling non-agent to make
  authenticated requests to the `A2AServer` of the _Magic 8-Ball Agent_.
2. **Nested Authentication:** _(`U -> A -> B [auth required]`)_ This scenario is for any architecture where the
  _Magic 8-Ball Agent_ **IS NOT** is nested beneath N different agents and **IS NOT** interacted with directly like the
  _Direct Authentication_ scenario.

## Architecture

Recently, A2A added support for its `A2AClient` to
[provide HTTP headers](https://github.com/google/A2A/commit/c0a40309c654f4b546213ad13b481d752bf46dfd) to the `A2AServer`
allowing for HTTP-based authentication/authorization. There were also changes to A2A which added support for
[OpenAPI Security Requirements/Schemes](https://github.com/google/A2A/commit/fec30cc986d8b6c337d6e99b881f376994157773)
in the `AgentCard`. This sample builds on top of both of these A2A enhancements, allowing the `AgentCard` to broadcast
its supported _Security Scheme(s)_ as well as which _Security Requirement(s)_ are necessary for an `A2AClient` to make
authenticated/authorized calls to the corresponding `A2AServer`.

The way this sample works is for the _Magic 8-Ball Agent_, its `AgentCard` is configured to support a single OAuth
_Security Scheme_ that uses Google OAuth, and there is a global the global _(`#/security`) Security Requirements_ that
requires all `A2AServer` API calls be authenticated using Google OAuth _(a Bearer Token provided by a Google OAuth
Client Application)_. To enforce this, the _Magic 8-Ball Agent_ `A2AServer` is started with a
[Starlette](https://www.starlette.io/) middlware registered that will process the global _(`#/security`) _Security Requirements (and related Security Schemes)_ of the `AgentCard`, and require a _Bearer Token_ header for each
`A2AServer` API calls.

Whenever the middleware fails to authenticate the API call, a `401` or `403` is returned _(based
on the presence of the Bearer Token header)_ and a JSON payload is provided with details on how to obtain a Google OAuth
Bearer Token:

* `error`: The single-word code of the issue _(`forbidden` in the case of a `403`, and `unauthorized` for a `401`)_
* `reason`: The human-readable summary of the error
* `hint`: The human-readable hint on how to get your credential
* `auth_url`: The OAuth authorization URL
* `state`: The OAuth `state` variable _(more on this shortly)_

Since the _Magic 8-Ball Agent_ is the only agent that should have access to the OAuth client id/secret required to
authenticate/authorize its `A2AServer` API calls, this sample uses a convention which enables calling
agents/applications to specify where the _Magic 8-Ball Agent_ should redirect the user after it completes the OAuth
handshake successfully. _(This is what allows the credentials, and optional application-level state to be sent to the
caller, or elsewhere.)_ The reason this convention is a requirement is for the following reasons:

1. The _Magic 8-Ball Agent_ needs to know how to provide the validated credentials _(and possibly some
  application-specific information provided by the `A2AServer` API caller)_ to the appropriate place after
  authenticating the API call
2. The _Magic 8-Ball Agent_ needs to be able to solve the first problem without exposing/requiring access to its OAuth
  client id/secret to other agentic components _(For example, without the ability for the Magic 8-Ball Agent allowing
  this level of configuration, the Personal Assistant Agent would need to have access to the OAuth client id/secret
  that the Magic 8-Ball Agent uses to handle the OAuth callback.)_
3. The _Magic 8-Ball Agent_ needs to be able to solve the first problem without requiring its OAuth Client application
  to be tightly-coupled to all of the different places it might need to redirect _(provide credentials)_ after
  authentication/authorization

The aforementioned convention utilizes the `OAUTH_CALLBACK` request header, which allows the calling agent/application
to tell the _Magic 8-Ball Agent_ where to send the credentials _(as well as optional application-level state)_ after successful OAuth handshake. The `OAUTH_CALLBACK` header is a JSON payload with the following structure:

* `redirect_uri`: The `redirect_uri` to be baked into the OAuth authorization URL _(must be known at authentication
  time)_
* `params`: A JSON object of key/value pairs of application-specific data to be sent to the `redirect_uri` after
  successful authentication/authorization by the _Magic 8-Ball Agent_ via its OAuth `/auth` callback handler

Once the _Magic 8-Ball Agent_ handles the OAuth handshake via OAuth callback _(`/auth`)_, the _Magic 8-Ball Agent_ will
redirect to the location provided by the `redirect_uri` value in the `OAUTH_CALLBACK` header, with the `state` query
variable set to Base64-encoded JSON payload of both the OAuth credentials _(`credentials`)_ and the `OAUTH_CALLBACK`
contents _(`oauth_callback`)_.

**Note:** Streaming is **DISABLED** for this sample for simplicity.

### Explanation of Cenvention

A perfect example of why this is required is for the Nested Authentication scenario
_(`U -> Demo UI -> Personal Assistant Agent -> Magic 8-Ball Agent [auth required]`)_ discussed below. For the
_Personal Assistant Agent_ to get the necessary information to configure its `A2AClient`, it needs to be provided with
the credentials provided to the _Magic 8-Ball Agent_ `A2AServer` OAuth callback handler. So how does this information
get to the appropriate place, and only the appropriate place? The _Magic 8-Ball Agent_ needs to know how to get the
credentials to the _Personal Assistant Agent_ and that's where this level of configurability is useful.

**Note:** Not only does the _Personal Assistant Agent_ need to be provided with the credentials, but for the Demo UI
sample below, the _Personal Assistant Agent_ also needs to know how to redirect back to the Demo UI, to the appropriate
conversation.

## Scenarios

All scenarios in this sample have an ADK Agent sitting behind an `A2AServer`, and a sample web UI for standalone
demonstration. In the case of the _Magic 8-Ball Agent_, it also has been configured to enforce the
_Security Requirements_ in its `AgentCard` using the aforementioned Starlette middleware.

### Direct Authentication

Direct Authentication is some application, user or agent needing to provide authentication credentials to the agent's
`A2AServer` directly. _(`U -> A [auth required]`)_

![Sequence Diagram for Demo UI](/samples/python/agents/google_adk_with_agent_auth/images/ua-scenario-seq-dia.svg)

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

![Sequence Diagram for Demo UI](/samples/python/agents/google_adk_with_agent_auth/images/uab-scenario-seq-dia.svg)

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
