## Extended Agent Card CLI with Basic Authentication

This CLI is a small host application designed to demonstrate the **extended agent card** capabilities of an A2AClient, specifically when using API key authentication via a pre-shared API key. It is intended to be used in conjunction with the `extended_agent_card_adk` sample agent.

The `extended_agent_card_adk` agent enables the `supportsAuthenticatedExtendedCard` field in its AgentCard. Both this CLI and the `extended_agent_card_adk` agent are configured to use an API key (expected to be sourced from the `EXTENDED_AGENT_CARD_API_KEY` environment variable set in your .env file) for authentication. The CLI sends this key in a request header, and the agent verifies it.

This CLI supports:
- Reading a server's standard AgentCard.
- Reading the authenticated extended AgentCard if the server supports it and authentication is successful.
- Text-based collaboration with the remote agent.

All content received from the A2A server is printed to the console.

The client will use streaming if the server supports it.

## Prerequisites

- Python 3.12 or higher
- UV
- A running `extended_agent_card_adk` server (which requires its own `EXTENDED_AGENT_CARD_API_KEY` set.
- The `EXTENDED_AGENT_CARD_API_KEY` environment variable must be set in your terminal session for this CLI to use for authentication. This key must match the one configured for the `extended_agent_card_adk` agent.

## Running the CLI

1.  **Start the `extended_agent_card_adk` agent:**
    *   Navigate to its directory:
        ```bash
        cd samples/python/agents/extended_agent_card_adk
        ```
    *   Ensure you have a `.env` file in that directory with your API key:
        ```bash
        echo "EXTENDED_AGENT_CARD_API_KEY=your_api_key_here" > .env
        ```
    *   Run the agent:
        ```bash
        uv run .
        ```
    *   Note the URL and port the agent is running on (e.g., `http://localhost:10002` or as configured).

2.  **Set up the API key for this CLI:**
    In the terminal where you will run this CLI, set the `EXTENDED_AGENT_CARD_API_KEY` environment variable. This key must match the one used by the `extended_agent_card_adk` agent.
    ```bash
    cd samples/python/hosts/cli
    ```
2. Run the example client
    ```
    uv run . --agent [url-of-your-a2a-server]
    ```

   for example `--agent http://localhost:10002`. More command line options are documented in the source code. 
