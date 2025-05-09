# Agent Skills: Defining What Your Agent Can Do

An **Agent Skill** describes a specific capability or function that an A2A agent can perform. Clients use this information, which is part of the Agent Card, to understand what tasks they can delegate to the agent and how to interact with it for specific purposes.

The A2A Python SDK provides the `AgentSkill` Pydantic model from `a2a.types` to define these skills. Let's examine how the HelloWorld agent defines its single skill in the `a2a-python-sdk/examples/helloworld/__main__.py` script:

```python
# From examples/helloworld/__main__.py

from a2a.types import (
    AgentAuthentication,
    AgentCapabilities,
    AgentCard,
    AgentSkill,  # This is the class we're focusing on
)

# ... inside the if __name__ == '__main__': block ...
    skill = AgentSkill(
        id='hello_world',
        name='Returns hello world',
        description='just returns hello world',
        tags=['hello world'],
        examples=['hi', 'hello world'],
    )
# ...
```

## Understanding `AgentSkill` Fields

The `AgentSkill` model has several important fields, as detailed in the [A2A Protocol Specification for AgentSkill](../specification.md#554-agentskill-object). Here's a breakdown of the fields used by the HelloWorld agent:

- `id` (string, required): A unique identifier for this skill within the context of this particular agent. The HelloWorld agent uses `"hello_world"`.
- `name` (string, required): A human-readable name for the skill. Here, it's `"Returns hello world"`.
- `description` (string, optional but recommended): A more detailed explanation of what the skill does. For HelloWorld, it's `"just returns hello world"`.
- `tags` (list of strings, optional): Keywords or categories that can help with discoverability and classification of the skill (e.g., `["hello world"]`).
- `examples` (list of strings, optional): Example prompts or use cases that illustrate how to use this skill. This helps clients (and potentially human users or other agents) understand how to formulate requests. HelloWorld provides `["hi", "hello world"]`.
- `inputModes` (list of strings, optional): Specifies the [MIME types](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types) this skill accepts as input. If omitted (as in this HelloWorld skill), it defaults to the `defaultInputModes` defined in the main `AgentCard`.
- `outputModes` (list of strings, optional): Specifies the MIME types this skill produces as output. If omitted, it defaults to the `defaultOutputModes` from the `AgentCard`.

In the HelloWorld example, the `AgentSkill` is straightforward:

- It identifies a single capability: responding with "hello world".
- The `inputModes` and `outputModes` are not specified at the skill level, meaning this skill will use the default modes defined in the `AgentCard` (which we'll see are `["text"]` in the next section).

Defining clear and descriptive skills, even for simple agents, is a good practice. It makes your agent more understandable and easier to integrate into larger systems.

In the next section, we'll see how this `AgentSkill` is incorporated into the full `AgentCard` for the HelloWorld agent.
