# 3. Agent Skills & Agent Card

Before an A2A agent can do anything, it needs to define what it _can_ do (its skills) and how other agents or clients can find out about these capabilities (its Agent Card).

We'll use the `helloworld` example located in [`a2a-samples/samples/python/agents/helloworld/`](https://github.com/google-a2a/a2a-samples/tree/main/samples/python/agents/helloworld).

## Agent Skills

An **Agent Skill** describes a specific capability or function the agent can perform. It's a building block that tells clients what kinds of tasks the agent is good for.

Key attributes of an `AgentSkill` (defined in `a2a.types`):

- `id`: A unique identifier for the skill.
- `name`: A human-readable name.
- `description`: A more detailed explanation of what the skill does.
- `tags`: Keywords for categorization and discovery.
- `examples`: Sample prompts or use cases.
- `inputModes` / `outputModes`: Supported Media Types for input and output (e.g., "text/plain", "application/json").

In `__main__.py`, you can see how a skill for the Helloworld agent is defined:

```python { .no-copy }
--8<-- "https://raw.githubusercontent.com/google-a2a/a2a-samples/refs/heads/main/samples/python/agents/helloworld/__main__.py:AgentSkill"
```

This skill is very simple: it's named "Returns hello world" and primarily deals with text.

## Agent Card

The **Agent Card** is a JSON document that an A2A Server makes available, typically at a `.well-known/agent.json` endpoint. It's like a digital business card for the agent.

Key attributes of an `AgentCard` (defined in `a2a.types`):

- `name`, `description`, `version`: Basic identity information.
- `url`: The endpoint where the A2A service can be reached.
- `capabilities`: Specifies supported A2A features like `streaming` or `pushNotifications`.
- `defaultInputModes` / `defaultOutputModes`: Default Media Types for the agent.
- `skills`: A list of `AgentSkill` objects that the agent offers.

The `helloworld` example defines its Agent Card like this:

```python { .no-copy }
--8<-- "https://raw.githubusercontent.com/google-a2a/a2a-samples/refs/heads/main/samples/python/agents/helloworld/__main__.py:AgentCard"
```

This card tells us the agent is named "Hello World Agent", runs at `http://localhost:9999/`, supports text interactions, and has the `hello_world` skill. It also indicates public authentication, meaning no specific credentials are required.

Understanding the Agent Card is crucial because it's how a client discovers an agent and learns how to interact with it.
