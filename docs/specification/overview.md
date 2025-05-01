## Overview

### Actors

The A2A protocol has three actors:

- **User**
  The end user (human or service) that is using an agentic system to accomplish tasks.
- **Client**
  The entity (service, agent, application) that is requesting an action from an opaque agent on behalf of the user.
- **Remote Agent (Server)**
  The opaque ("black box") agent which is the A2A server.

### Transport

The protocol leverages HTTP for transport between the client and the remote agent. Depending on the capabilities of the client and the remote agent, they may leverage SSE for supporting streaming for receiving updates from the server.

A2A leverages [JSON-RPC 2.0](https://www.jsonrpc.org/specification) as the data exchange format for communication between a Client and a Remote Agent.

### Async

A2A clients and servers can use standard request/response patterns and poll for updates. However, A2A also supports streaming updates through SSE (while connected) and receiving [push notifications](/topics/push_notifications.md?id=remote-agent-to-client-updates) while disconnected.

### Authentication and Authorization

A2A models agents as enterprise applications (and can do so because A2A agents are opaque and do not share tools and resources). This quickly brings enterprise-readiness to agentic interop.

A2A follows [OpenAPI's Authentication specification](https://swagger.io/docs/specification/v3_0/authentication/) for authentication. Importantly, A2A agents do not exchange identity information within the A2A protocol. Instead, they obtain materials (such as tokens) out of band and transmit materials in HTTP headers and not in A2A payloads.

While A2A does not transmit identity in-band, servers do send authentication requirements in A2A payloads. At minimum, servers are expected to publish their requirements in their [Agent Card](#agent-card). Thoughts about discovering agent cards are in [this topic](topics/agent_discovery.md?id=discovering-agent-cards).

Clients should use one of the servers published authentication protocols to authenticate their identity and obtain credential material. A2A servers should authenticate **every** request and reject or challenge requests with standard HTTP response codes (401, 403), and authentication-protocol-specific headers and bodies (such as a HTTP 401 response with a [WWW-Authenticate](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/WWW-Authenticate) header indicating the required authentication schema, or OIDC discovery document at a well-known path). More details discussed in [Enterprise Ready](topics/enterprise_ready.md).

> Note: If an agent requires that the client/user provide additional credentials during execution of a task (for example, to use a specific tool), the agent should return a task status of `Input-Required` with the payload being an Authentication structure. The client should, again, obtain credential material out of band to A2A.
