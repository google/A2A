## Extended Agent Card ADK Agent

This sample uses the Agent Development Kit (ADK) to create an agent that demonstrates the **authenticated extended agent card** feature. It is hosted as an A2A server.

This agent enables the `supportsAuthenticatedExtendedCard` field in its AgentCard. It expects an API key in the `X-API-KEY` header for requests to its authenticated extended card endpoint. This API key is configured via the `EXTENDED_AGENT_CARD_API_KEY` environment variable, typically loaded from a `.env` file in this agent's directory.

It is designed to be used with a client like the `extended_agent_card_cli` sample.

## Prerequisites

- Python 3.9 or higher
- UV
- An API key to be used for securing the extended agent card endpoint. This key will be shared with the client.
- (Optional) Access to an LLM and its API Key (e.g., `GOOGLE_API_KEY`) if you extend this agent to use LLM capabilities. This sample primarily focuses on the extended card mechanism.


## Running the Sample

1.  **Set up the API key for the Agent:**
    *   Navigate to this agent's directory:
        ```bash
        cd samples/python/agents/extended_agent_card_adk
        ```
    *   Create a `.env` file in this directory.
    *   Add your chosen API key to the `.env` file. This key will be used by the agent to verify incoming requests for the extended card. The client (e.g., `extended_agent_card_cli`) will need to send this exact key.
        Example content for `samples/python/agents/extended_agent_card_adk/.env`:
        ```env
        EXTENDED_AGENT_CARD_API_KEY=your_shared_api_key_here
        # If you are using Google Generative AI services directly (not Vertex AI), also add:
        # GOOGLE_API_KEY=your_google_api_key_for_genai_services
        ```
        *(Replace `your_shared_api_key_here` with your actual key)*

2.  Run the agent:
    ```bash
    uv run .
    ```
    *   The agent will typically start on `http://localhost:10002` by default. Check the console output for the exact URL and port.

3.  In a separate terminal, run a compatible A2A client, such as the `extended_agent_card_cli`:
    ```
    # Navigate to the CLI's directory
    cd samples/python/hosts/extended_agent_card_cli

    # Ensure the CLI's EXTENDED_AGENT_CARD_API_KEY (from its .env or environment) matches the agent's.
    # Connect to this agent (e.g., on port 10002)
    uv run . --agent http://localhost:10002
    ```
