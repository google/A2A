# Agent2Agent (A2A) Protocol

![PyPI - Version](https://img.shields.io/pypi/v/a2a-sdk)
[![Apache License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

![A2A Banner](docs/assets/a2a-banner.png)

**An open protocol enabling communication and interoperability between opaque agentic applications.**

The Agent2Agent (A2A) protocol addresses a critical challenge in the AI landscape: enabling gen AI agents, built on diverse frameworks by different companies running on separate servers, to communicate and collaborate effectively - as agents, not just as tools. A2A aims to provide a common language for agents, fostering a more interconnected, powerful, and innovative AI ecosystem.

With A2A, agents can:

- Discover each other's capabilities.
- Negotiate interaction modalities (text, forms, media).
- Securely collaborate on long running tasks.
- Operate without exposing their internal state, memory, or tools.

## Intro to A2A Video

[![A2A Intro Video](docs/assets/a2a-video-thumbnail.png)](https://goo.gle/a2a-video)

## Why A2A?

As AI agents become more prevalent, their ability to interoperate is crucial for building complex, multi-functional applications. A2A aims to:

- **Break Down Silos:** Connect agents across different ecosystems.
- **Enable Complex Collaboration:** Allow specialized agents to work together on tasks that a single agent cannot handle alone.
- **Promote Open Standards:** Foster a community-driven approach to agent communication, encouraging innovation and broad adoption.
- **Preserve Opacity:** Allow agents to collaborate without needing to share internal memory, proprietary logic, or specific tool implementations, enhancing security and protecting intellectual property.

### Key Features

- **Standardized Communication:** JSON-RPC 2.0 over HTTP(S).
- **Agent Discovery:** Via "Agent Cards" detailing capabilities and connection info.
- **Flexible Interaction:** Supports synchronous request/response, streaming (SSE), and asynchronous push notifications.
- **Rich Data Exchange:** Handles text, files, and structured JSON data.
- **Enterprise-Ready:** Designed with security, authentication, and observability in mind.

## Getting Started

- 📚 **Explore the Documentation:** Visit the [Agent2Agent Protocol Documentation Site](https://goo.gle/a2a) for a complete overview, the full protocol specification, tutorials, and guides.
- 📝 **View the Specification:** [A2A Protocol Specification](https://google-a2a.github.io/A2A/specification/)
- 🐍 Use the [A2A Python SDK](https://github.com/google-a2a/a2a-python)
    - `pip install a2a-sdk`
- 🎬 Use our [samples](https://github.com/google-a2a/a2a-samples) to see A2A in action

## Local Agent Development and Handshake

This repository includes a minimal A2A agent example to help you understand local development and the basic A2A handshake process.

### Running the Minimal Agent Example

The example agent is located at `ionverse/libs/a2a_example.py`.

1.  **Install Dependencies:**
    Ensure you have the necessary Python packages installed. If you haven't already, create and activate a virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Run the Agent:**
    Execute the example script:
    ```bash
    python ionverse/libs/a2a_example.py
    ```
    The agent will start and listen on `http://localhost:8000/`. You should see output similar to:
    ```console
    INFO:     Started server process [xxxxx]
    INFO:     Waiting for application startup.
    INFO:     Application startup complete.
    INFO:     Uvicorn running on http://localhost:8000 (Press CTRL+C to quit)
    ```

### Understanding the Handshake

The A2A interaction model, even locally, follows these key steps:

1.  **Agent Discovery (Agent Card):**
    A client discovers an agent's capabilities by fetching its **Agent Card**. The minimal example agent exposes its card at:
    `http://localhost:8000/.well-known/agent.json`

    You can try opening this URL in your browser or using `curl`:
    ```bash
    curl http://localhost:8000/.well-known/agent.json
    ```
    This JSON response describes the agent (name, description, URL, skills, capabilities, etc.). The `Minimal A2A Agent` has a skill with `id: 'minimal_echo'`.

2.  **Initiating a Task (Message Send):**
    Once a client knows about an agent and its skills, it can send messages to initiate tasks. A2A uses JSON-RPC 2.0 over HTTP. For the `minimal_echo` skill, a client would send a request to the agent's URL (`http://localhost:8000/`) to invoke this skill.

    For example, to send a simple text message, the client would construct a JSON-RPC request like this (conceptual example):
    ```json
    {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "messageId": "client-message-123",
                "role": "user",
                "parts": [
                    {
                        "type": "TextPart",
                        "text": "Hello Agent!"
                    }
                ]
            }
            // Optionally, specify skillId if the agent has multiple skills
            // and the default isn't desired, or to be explicit.
            // "skillId": "minimal_echo"
        },
        "id": "rpc-request-1"
    }
    ```
    The agent would then process this and respond, in the case of our minimal agent, with "Hello from Minimal A2A Agent!".

    *Note: Interacting via `curl` for anything beyond fetching the Agent Card can be complex due to JSON-RPC formatting. Typically, you'd use an A2A client library or tool.*

This example provides a basic illustration of how an A2A agent advertises its capabilities and how a client might begin an interaction. Refer to the full [A2A Protocol Specification](https://google-a2a.github.io/A2A/specification/) for detailed information on all methods, task lifecycles, and data types.

## Contributing

We welcome community contributions to enhance and evolve the A2A protocol!

- **Questions & Discussions:** Join our [GitHub Discussions](https://github.com/google-a2a/A2A/discussions).
- **Issues & Feedback:** Report issues or suggest improvements via [GitHub Issues](https://github.com/google-a2a/A2A/issues).
- **Contribution Guide:** See our [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute.
- **Private Feedback:** Use this [Google Form](https://goo.gle/a2a-feedback).
- **Partner Program:** Google Cloud customers can join our partner program via this [form](https://goo.gle/a2a-partner).

## What's next

### Protocol Enhancements

- **Agent Discovery:**
    - Formalize inclusion of authorization schemes and optional credentials directly within the `AgentCard`.
- **Agent Collaboration:**
    - Investigate a `QuerySkill()` method for dynamically checking unsupported or unanticipated skills.
- **Task Lifecycle & UX:**
    - Support for dynamic UX negotiation _within_ a task (e.g., agent adding audio/video mid-conversation).
- **Client Methods & Transport:**
    - Explore extending support to client-initiated methods (beyond task management).
    - Improvements to streaming reliability and push notification mechanisms.

## About

The A2A Protocol is an open-source project by Google LLC, under the [Apache License 2.0](LICENSE), and is open to contributions from the community.
