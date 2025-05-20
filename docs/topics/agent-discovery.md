# Agent Discovery in A2A

For AI agents to collaborate using the Agent2Agent (A2A) protocol, they first need to find each other and understand what capabilities the other agents offer. A2A standardizes the format of an agent's self-description through the **[Agent Card](../specification.md#5-agent-discovery-the-agent-card)**. However, the methods for discovering these Agent Cards can vary depending on the environment and requirements.

## The Role of the Agent Card

The Agent Card is a JSON document that serves as a digital "business card" for an A2A Server (the remote agent). It is crucial for discovery and initiating interaction. Key information typically included in an Agent Card:

- **Identity:** `name`, `description`, `provider` information.
- **Service Endpoint:** The `url` where the A2A service can be reached.
- **A2A Capabilities:** Supported protocol features like `streaming` or `pushNotifications`.
- **Authentication:** Required authentication `schemes` (e.g., "Bearer", "OAuth2") to interact with the agent.
- **Skills:** A list of specific tasks or functions the agent can perform (`AgentSkill` objects), including their `id`, `name`, `description`, `inputModes`, `outputModes`, and `examples`.

Client agents parse the Agent Card to determine if a remote agent is suitable for a given task, how to structure requests for its skills, and how to communicate with it securely.

## Discovery Strategies

Here are common strategies for how a client agent might discover the Agent Card of a remote agent:

### 1. Well-Known URI

This is a recommended approach for public agents or agents intended for broad discoverability within a specific domain.

- **Mechanism:** A2A Servers host their Agent Card at a standardized, "well-known" path on their domain.
- **Standard Path:** `https://{agent-server-domain}/.well-known/agent.json` (following the principles of [RFC 8615](https://www.ietf.org/rfc/rfc8615.txt) for well-known URIs).
- **Process:**
    1. A client agent knows or programmatically discovers the domain of a potential A2A Server (e.g., `smart-thermostat.example.com`).
    2. The client performs an HTTP `GET` request to `https://smart-thermostat.example.com/.well-known/agent.json`.
    3. If the Agent Card exists and is accessible, the server returns it as a JSON response.
- **Advantages:** Simple, standardized, and enables automated discovery by crawlers or systems that can resolve domains. Effectively reduces the discovery problem to "find the agent's domain."
- **Considerations:** Best suited for agents intended for open discovery or discovery within an organization that controls the domain. The endpoint serving the Agent Card may itself require authentication if the card contains sensitive information.

### 2. Curated Registries (Catalog-Based Discovery)

For enterprise environments, marketplaces, or specialized ecosystems, Agent Cards can be published to and discovered via a central registry or catalog.

- **Mechanism:** An intermediary service (the registry) maintains a collection of Agent Cards. Clients query this registry to find agents based on various criteria (e.g., skills offered, tags, provider name, desired capabilities).
- **Process:**
    1. A2A Servers (or their administrators) register their Agent Cards with the registry service. The mechanism for this registration is outside the scope of the A2A protocol itself.
    2. Client agents query the registry's API (e.g., "find agents with 'image-generation' skill that support streaming").
    3. The registry returns a list of matching Agent Cards or references to them.
- **Advantages:**
    - Centralized management, curation, and governance of available agents.
    - Facilitates discovery based on functional capabilities rather than just domain names.
    - Can implement access controls, policies, and trust mechanisms at the registry level.
    - Enables scenarios like company-specific or team-specific agent catalogs, or public marketplaces of A2A-compliant agents.
- **Considerations:** Requires an additional registry service. The A2A protocol does not currently define a standard API for such registries, though this is an area of potential future exploration and community standardization.

### 3. Direct Configuration / Private Discovery

In many scenarios, especially within tightly coupled systems, for private agents, or during development and testing, clients might be directly configured with Agent Card information or a URL to fetch it.

- **Mechanism:** The client application has hardcoded Agent Card details, reads them from a local configuration file, receives them through an environment variable, or fetches them from a private, proprietary API endpoint known to the client.
- **Process:** This is highly specific to the application's deployment and configuration strategy.
- **Advantages:** Simple and effective for known, static relationships between agents or when dynamic discovery is not a requirement.
- **Considerations:** Less flexible for discovering new or updated agents dynamically. Changes to the remote agent's card might require re-configuration of the client. Proprietary API-based discovery is not standardized by A2A.

## Securing Agent Cards

Agent Cards themselves can sometimes contain information that should be protected, such as:

- The `url` of an internal-only or restricted-access agent.
- Details in the `authentication.credentials` field if it's used for scheme-specific, non-secret information (e.g., an OAuth token URL). Storing actual plaintext secrets in an Agent Card is **strongly discouraged**.
- Descriptions of sensitive or internal skills.

**Protection Mechanisms:**

- **Access Control on the Endpoint:** The HTTP endpoint serving the Agent Card (whether it's the `/.well-known/agent.json` path, a registry API, or a custom URL) should be secured using standard web practices if the card is not intended for public, unauthenticated access.
    - **mTLS:** Require mutual TLS for client authentication if appropriate for the trust model.
    - **Network Restrictions:** Limit access to specific IP ranges, VPCs, or private networks.
    - **Authentication:** Require standard HTTP authentication (e.g., OAuth 2.0 Bearer token, API Key) to access the Agent Card itself.
- **Selective Disclosure by Registries:** Agent registries can implement logic to return different Agent Cards or varying levels of detail based on the authenticated client's identity and permissions. For example, a public query might return a limited card, while an authenticated partner query might receive a card with more details.

It's crucial to remember that if an Agent Card were to contain sensitive data (again, **not recommended** for secrets), the card itself **must never** be available without strong authentication and authorization. The A2A protocol encourages authentication schemes where the client obtains dynamic credentials out-of-band, rather than relying on static secrets embedded in the Agent Card.

## Future Considerations

The A2A community may explore standardizing aspects of registry interactions or more advanced, semantic discovery protocols in the future. Feedback and contributions in this area are welcome to enhance the discoverability and interoperability of A2A agents.
