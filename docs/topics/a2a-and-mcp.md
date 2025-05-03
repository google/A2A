# Using Agent-to-Agent with MCP

## A2A ❤️ MCP

**TL;DR;** Agentic applications need both A2A and MCP. We recommend MCP for tools and A2A for agents.

## Why Protocols?

Standard protocols are essential for enabling agentic interoperability, particularly in connecting agents to external systems. This is critical in two interconnected areas of innovation: Tools and Agents.

**Tools** are primitives with structured inputs and outputs and (typically) well-known behavior. **Agents** are autonomous applications that can accomplish novel tasks by using tools, reasoning, and user interactions. Agentic applications must use both tools **and** agents to accomplish goals for their users.

## Complementary

[Model Context Protocol](https://modelcontextprotocol.io/) (MCP) is the emerging standard for connecting LLMs with data, resources, and tools. We already observe MCP standardizing 'function calling' across different models and frameworks. This is creating an ecosystem of tool service providers and dramatically lowering the complexity to connect agents with tools and data. We expect this trend to continue as more frameworks, service providers, and platforms adopt MCP.

A2A is focused on a different problem. A2A is an application level protocol that enables agents to collaborate in their natural modalities. It allows agents to communicate as _agents_ (or as users) instead of as tools. We hope that A2A gains adoption as a complement to MCP that enables ecosystems of agents and will be working in the open with the community to make this happen.

## Example

Let's look at an example:

> Consider an auto repair shop that fixes cars. The shop employs autonomous workers who use special-purpose tools (such as vehicle jacks, multimeters, and socket wrenches) to diagnose and repair problems. The workers often have to diagnose and repair problems they have not seen before. The repair process can involve extensive conversations with a customer, research, and working with part suppliers.

Now let's model the shop employees as AI agents:

- MCP is the protocol to connect these agents with their structured tools (e.g. `raise platform by 2 meters`, `turn wrench 4 mm to the right`).

- A2A is the protocol that enables end users or other agents to work with the shop employees (_"my car is making a rattling noise"_). A2A enables ongoing back-and-forth communication and an evolving plan to achieve results (_"send me a picture of the left wheel"_, _"I notice fluid leaking. How long has that been happening?"_). A2A also helps the auto shop employees work with other agents such as their part suppliers.

## Intersection

We recommend that applications model A2A agents as MCP resources (represented by their [AgentCard](/documentation.md#agent-card)). The frameworks can then use A2A to communicate with their user, the remote agents, and other agents.

![Agentic Application showing A2A and MCP together](../assets/a2a-mcp.png)
