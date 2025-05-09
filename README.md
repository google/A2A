# Agent2Agent (A2A) Protocol

![A2A Banner](docs/assets/a2a-banner.png)
[![Apache License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

**An open protocol enabling communication and interoperability between opaque agentic applications.**

The Agent2Agent (A2A) protocol addresses a critical challenge in the AI landscape: enabling gen AI agents, built on diverse frameworks by different companies running on separate servers, to communicate and collaborate effectively - as agents, not just as tools. A2A aims to provide a common language for agents, fostering a more interconnected, powerful, and innovative AI ecosystem.

With A2A, agents can:

- Discover each other's capabilities.
- Negotiate interaction modalities (text, forms, media).
- Securely collaborate on long running tasks.
- Operate without exposing their internal state, memory, or tools.

## See A2A in Action

Watch [this demo video](https://storage.googleapis.com/gweb-developer-goog-blog-assets/original_videos/A2A_demo_v4.mp4) to see how A2A enables seamless communication between different agent frameworks.

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

- 📚 **Explore the Documentation:** Visit the [Agent2Agent Protocol Documentation Site](https://google.github.io/A2A/) for a complete overview, the full protocol specification, tutorials, and guides.
- 📝 **View the Specification:** [A2A Protocol Specification](https://google.github.io/A2A/specification/)
- 🎬 Use our [samples](/samples) to see A2A in action
  - Sample A2A Client/Server ([Python](/samples/python/common), [JS](/samples/js/src))
  - [Multi-Agent Web App](/demo/README.md)
  - CLI ([Python](/samples/python/hosts/cli/README.md), [JS](/samples/js/README.md))
- 🤖 Use our [sample agents](/samples/python/agents/README.md) to see how to bring A2A to agent frameworks
  - [Agent Development Kit (ADK)](/samples/python/agents/google_adk/README.md)
  - [CrewAI](/samples/python/agents/crewai/README.md)
  - [Enterprise Data Agent (Gemini + Mindsdb)](/samples/python/agents/mindsdb/README.md)
  - [LangGraph](/samples/python/agents/langgraph/README.md)
  - [Genkit](/samples/js/src/agents/README.md)
  - [LlamaIndex](/samples/python/agents/llama_index_file_chat/README.md)
  - [Marvin](/samples/python/agents/marvin/README.md)
  - [Semantic Kernel](/samples/python/agents/semantickernel/README.md)
  - [AG2 + MCP](/samples/python/agents/ag2/README.md)
- 📑 Review key topics to understand protocol details
  - [A2A and MCP](https://google.github.io/A2A/topics/a2a-and-mcp/)
  - [Agent Discovery](https://google.github.io/A2A/topics/agent-discovery/)
  - [Enterprise Ready](https://google.github.io/A2A/topics/enterprise-ready/)
  - [Push Notifications](https://google.github.io/A2A/topics/streaming-and-async/#2-push-notifications-for-disconnected-scenarios)

## Contributing

We welcome community contributions to enhance and evolve the A2A protocol!

- **Questions & Discussions:** Join our [GitHub Discussions](https://github.com/google/A2A/discussions).
- **Issues & Feedback:** Report issues or suggest improvements via [GitHub Issues](https://github.com/google/A2A/issues).
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
