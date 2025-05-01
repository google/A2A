# Agent-level Authentication/Authorization via Google ADK and Google OAuth

This sample uses the Agent Development Kit (ADK) to create a simple agent that uses uses A2A and Google OAuth to secure
access to your agent.

## Prerequisites

- Python 3.12 or higher
- [UV](https://docs.astral.sh/uv/)
- Access to an LLM and API Key
- Access to a [Google OAuth Application](https://developers.google.com/identity/protocols/oauth2)

## Architecture

This sample comes with a Python-based `A2AServer` that has been extended to have an OAuth callback handler, as well as a
simple Web UI for signing in with Google and authorizing your OAuth Client application _(to get your Bearer Token)_. No
modifications were made to the `A2AServer` API/handlers, the extensions were made directly to the HTTP Server that the
`A2AServer` builds upon _(Starlette: [https://www.starlette.io/])_.

To enforce authentication of the `A2AServer`, a sample Starlette middleware was created that wires up authentication
based on the global _(`#/security`) Security Requirements_ in the `AgentCard`.

## Running the Sample

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
    uv run .
    ```

4. Interact with the agent:

    - `curl`

        - Make the unauthenticated call

        ```text
        curl -X POST -d '{
          "jsonrpc": "2.0",
          "id": 1,
          "method": "tasks/send",
          "params": {
            "id": "t1",
            "sessionId": "fa09c65ea23a4ee59f9f2017ea01183a",
            "message": {
              "role": "user",
              "parts": [
                {
                "type": "text",
                "text": "Magic 8-ball, will I win the lottery?"
                }
              ]
            }
          }
        }' http://localhost:10002/
        ```

        You should get an authorization error back that looks like this:

        ```json
        {
            "error": "unauthorized",
            "reason": "Missing or malformed Authorization header.",
            "hint": "Get your Bearer Token via http://localhost:10002/whoami"
        }
        ```

        - Visit the URL in `hint` _([http://localhost:10002/whoami])_ so you can get your access token by signing in
        with Google and authorizing your OAuth application, and rendering a page with profile details and the Bearer
        Token

        - Make the authenticated call

        ```text
        curl -X POST -d '{
          "jsonrpc": "2.0",
          "id": 1,
          "method": "tasks/send",
          "params": {
            "id": "t1",
            "sessionId": "fa09c65ea23a4ee59f9f2017ea01183a",
            "message": {
              "role": "user",
              "parts": [
                {
                "type": "text",
                "text": "Magic 8-ball, will I win the lottery?"
                }
              ]
            }
          }
        }' -H 'Authorization: Bearer {YOUR_BEARER_TOKEN}' http://localhost:10002/
        ```

        You should get a response back that looks like this:

        ```json
        {
          "jsonrpc": "2.0",
          "id": 1,
          "result": {
            "id": "t1",
            "sessionId": "fa09c65ea23a4ee59f9f2017ea01183a",
            "status": {
              "state": "completed",
              "message": {
                "role": "agent",
                "parts": [
                  {
                    "type": "text",
                    "text": "Don't count on it\n"
                  }
                ]
              },
              "timestamp": "2025-05-01T11:14:45.484894"
            },
            "artifacts": [
              {
                "parts": [
                  {
                    "type": "text",
                    "text": "Don't count on it\n"
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
                    "text": "Magic 8-ball, will I win the lottery"
                  }
                ]
              }
            ]
          }
        }
        ```

    - `A2AClient` _(TBD, waiting on the SDK to firm up)_
