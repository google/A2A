# Agent Card: Describing Your Agent to the World

The **Agent Card** is a crucial JSON document that an A2A Server publishes. It serves as a comprehensive "digital business card" for the agent, providing all necessary information for other agents or clients to:

- Discover the agent.
- Understand its general purpose and specific capabilities (skills).
- Know how to communicate with it (e.g., its URL, supported modalities).
- Understand its authentication requirements.

The A2A Python SDK uses the `AgentCard` Pydantic model from `a2a.types`. Let's examine how the HelloWorld agent's card is defined in `a2a-python-sdk/examples/helloworld/__main__.py`:

```python
# From examples/helloworld/__main__.py

from a2a.types import (
    AgentAuthentication,
    AgentCapabilities,
    AgentCard, # This is the class we're focusing on
    AgentSkill,
)

# ... (skill definition from previous section) ...
# if __name__ == '__main__':
    skill = AgentSkill(
        id='hello_world',
        name='Returns hello world',
        description='just returns hello world',
        tags=['hello world'],
        examples=['hi', 'hello world'],
    )

    agent_card = AgentCard(
        name='Hello World Agent',
        description='Just a hello world agent',
        url='http://localhost:9999/', # The URL where the agent's A2A service listens
        version='1.0.0',
        defaultInputModes=['text'],   # Default input MIME type is plain text
        defaultOutputModes=['text'],  # Default output MIME type is plain text
        capabilities=AgentCapabilities(), # Basic capabilities, all options default to false/None
        skills=[skill],                   # Includes the 'hello_world' skill defined above
        authentication=AgentAuthentication(schemes=['public']), # Indicates it's publicly accessible
    )
# ...
```

## Key Components of the `AgentCard`

You can find the full details in the [A2A Protocol Specification for AgentCard](../specification.md#55-agentcard-object-structure). Here are the key fields used in our HelloWorld example:

- `name` (string, required): A human-readable name for the agent (e.g., `"Hello World Agent"`).
- `description` (string, optional): A human-readable description of the agent's general purpose.
- `url` (string, required): The base URL endpoint where the agent's A2A service listens for JSON-RPC requests. For our local HelloWorld example, this is `http://localhost:9999/`. The A2A server will typically serve requests at this base URL.
- `version` (string, required): The version string for the agent (e.g., `"1.0.0"`).
- `defaultInputModes` (list of strings, optional): An array of [MIME types](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types) the agent generally accepts as input across all its skills, unless overridden by a specific skill. If omitted, it typically defaults to `["text/plain"]`. Our example explicitly sets it to `["text"]`.
- `defaultOutputModes` (list of strings, optional): An array of MIME types the agent generally produces as output. Similar to `defaultInputModes`, it defaults to `["text/plain"]` if omitted. Our example sets it to `["text"]`.
- `capabilities` ([`AgentCapabilities`](../specification.md#552-agentcapabilities-object), required): Specifies optional A2A protocol features supported by the agent.
  - `streaming`: Boolean indicating if the agent supports Server-Sent Events (SSE) for methods like `message/sendStream`.
  - `pushNotifications`: Boolean indicating if the agent supports asynchronous push notifications to a client webhook.
  - `stateTransitionHistory`: Boolean indicating if detailed task state history is available.
  - In our HelloWorld example, `AgentCapabilities()` is used, meaning all these capabilities default to `None` or `False`. The HelloWorld agent *does* implement streaming, so to accurately reflect this, we would ideally set `capabilities=AgentCapabilities(streaming=True)`. We will address this when we explicitly cover streaming.
- `skills` (list of [`AgentSkill`](../specification.md#554-agentskill-object), required): An array listing all the specific skills the agent offers. We include the `hello_world` skill defined in the previous section.
- `authentication` ([`AgentAuthentication`](../specification.md#553-agentauthentication-object), optional): Describes the authentication schemes required to interact with the agent.
  - `schemes`: A list of supported authentication scheme names (e.g., `"Bearer"`, `"Basic"`).
  - Our HelloWorld agent uses `AgentAuthentication(schemes=['public'])`. The `"public"` scheme is a convention indicating that no specific authentication headers are required, making the agent publicly accessible (suitable for local testing or universally available agents).

When an A2A client wants to interact with an agent, it typically first fetches this Agent Card (often from a well-known path like `/.well-known/agent.json` appended to the agent's base URL). This card provides the client with all the information it needs to correctly format requests and understand the agent's capabilities. The `A2AServer` in the SDK automatically handles serving this card at the conventional path.

With the agent's skills and its descriptive card defined, we are now ready to look at how the server logic is implemented to handle incoming requests.
