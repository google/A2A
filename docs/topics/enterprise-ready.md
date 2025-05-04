# Enterprise Readiness

<!-- TOC -->

- [Enterprise Readiness](#enterprise-readiness)
  - [Transport Level Security](#transport-level-security)
  - [Server Identity](#server-identity)
  - [Client and User Identity](#client-and-user-identity)
  - [Authenticating Clients](#authenticating-clients)
  - [Authorization and Data Privacy](#authorization-and-data-privacy)
  - [Tracing and Observability](#tracing-and-observability)

<!-- /TOC -->

A2A **does not** want to invent any new standards for enterprise security and instead seamlessly integrate with existing infrastructure.

A2A models Enterprise Agents as standard, HTTP-based, enterprise applications and therefore relies on enterprise-standard auth, security, privacy, tracing, and monitoring. This is possible because A2A agents are opaque and do not share tools or resources (and therefore "single application" client/server best practices apply).

In fact, A2A keeps most enterprise concerns out of the protocol and instead require enterprise-grade HTTP with Open Authentication and Open Tracing support. Implementers should follow all enterprise best practices as it relates to application and user-level security.

## Transport Level Security

A2A is built on HTTP and any production installation should require HTTPS using modern TLS ciphers.

## Server Identity

A2A Servers present their identity in the form of digital certificates signed by well-known certificate authorities as part of the TLS negotiation. A2A Clients should verify server identity during connection establishment.

## Client and User Identity

There is no concept of a user or client identifier in A2A schemas. Instead, A2A conveys authentication requirements (scheme and materials) through the protocol. The client is responsible for negotiating with the appropriate authentication authority (out of band to A2A) and retrieving/storing credential materials (such as OAuth tokens). Those credential materials will be transmitted in HTTP headers and not in any A2A payload.

Different authentication protocols and service providers have different requirements and individual requests may require multiple identifiers and identities in scheme specific headers. It is recommended that clients always present a client identity (representing the client agent) and user identity (representing their user) in requests to A2A servers.

**Note**: Multi-identity federation is an open topic for discussion. For example, User U is working with Agent A requiring A-system's identifier. If Agent A then depends on Tool B or Agent B which requires B-system identifier, the user may need to provide identities for both A-system and B-system in a single request. (Assume A-system is an enterprise LDAP identity and B-system is a SaaS-provider identity).

It is currently recommended that if Agent A requires the user/client to provide an alternate identity for part of a task, it sends an update in the `INPUT-REQUIRED` state with the specific authentication requirements (in the same structure as an AgentCard's authentication requirements) to the client. The client then, out of band to A2A and also out of band to A-system, negotiates with B-system's authority to obtain credential material. Those materials (such as tokens) can be passed through Agent A to Agent B. Agent B will exchange when speaking to its upstream systems.

## Authenticating Clients

A2A servers are expected to publish supported and required authentication protocol(s) in its [Agent Card](/documentation.md#agent-card). These protocols should be one of the standard [OpenAPI Authentication formats](https://swagger.io/docs/specification/v3_0/authentication/) (such as API Keys, OAuth, OIDC, etc) but can be extended to another protocol supported by both client and server.

Individual authentication protocols have their own mechanisms for acquiring, refreshing, and challenging credential material (such as bearer or session tokens). The credential acquisition and maintenance process is considered external to A2A.

A2A servers are expected to authenticate **every** request and reject or challenge requests with standard HTTP response codes (401, 403), and authentication-protocol-specific headers and bodies (such as a HTTP 401 response with a [WWW-Authenticate](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/WWW-Authenticate) header indicating the required authentication schema, or OIDC discovery document at a well-known path).

## Authorization and Data Privacy

A2A servers are expected to authorize requests based on both the user and application identity. We recommend that individual agents manage access on at least two axes:

- **Skills**  
  Agents are expected to advertise (via an [Agent Card](/documentation.md#agent-card)) their capabilities in the form of skills. It is recommended that agents authorize on a per-skill basis (for example, OAuthScope 'foo-read-only' could limit access only to 'generateRecipe' skills).

- **Tools (Actions and Data)**  
  It is recommended that Agents restrict access to sensitive data or actions by placing them behind Tools. When an agentic flow or model needs to access this data, the agent should authorize access to a tool based on the application+user priviledge. We highly recommend utilizing API Management with Tool access.

## Tracing and Observability

As all A2A requests are 'standard' HTTP requests, both client and server should use their enterprise standard tooling and infrastructure which ideally adds appropriate instrumentation headers and writes events to standard logs and event queues.
