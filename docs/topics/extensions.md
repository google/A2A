# Extensions

## Abstract

Extensions are a means of extending the Agent2Agent (A2A) protocol with new data, requirements, methods, and state machines. Agents declare their support for extensions in their [`AgentCard`](/specification/#5-agent-discovery-the-agent-card), and clients can then opt-in to the behavior offered by the extension as part of requests they make to the agent. Extensions are identified by a URI and defined by their extension specification. Anyone is able to define, publish, and implement an extension.

## Introduction

The core A2A protocol is a solid basis for enabling communication between agents. However, it's clear that some domains require additional structure than what is offered by the generic methods in the protocol. Extensions were added to the protocol to help support these cases: with extensions, agents and clients can negotiate additional, custom logic to be layered on top of the core protocol.

### Scope of Extensions

The exact set of possible ways to use extensions is intentionally not defined. This is to facilitate the ability to use extensions to expand A2A beyond currently known use cases. However, some use cases are clearly forseeable, such as:

- Exposing new information in the `AgentCard`. An extension may not impact the request/response flow at all -- it can be simply used as a way to convey additional structured information to clients via the `AgentCard`. We refer to these as *data-only extensions*. For example, an extension could add structured data about an agent's GDPR compliance to its `AgentCard`.

- Overlaying additional structure and state change requirements on the core request/response messages. An extension could, for example, require that all messages use `DataPart`s that adhere to a specific schema. This type of extension effectively acts as a profile on the core A2A protocol, narrowing the space of allowed values. We refer to these as *profile extensions*. For example, a healthcare extension could mandate that all `Message` parts containing patient information must be encrypted and placed within a `DataPart` that conforms to a FHIR standard.

- Adding new RPC methods entirely. Extensions may define that the agent implements more than the core set of protocol methods. We refer to these as *method extensions*. For example, a ['task-history' extension](https://github.com/google-a2a/A2A/issues/585#:~:text=Details%20with%20an%20example) might add a `tasks/search` RPC method to retrieve a list of previous tasks.

There are some changes to the protocol that extensions *do not* allow. These are:

- Changing the definition of core data structures. Adding new fields or removing required fields to protocol-defined data structures is not supported. Extensions are expected to place custom attributes in the `metadata` map that is present on core data structures.
- Adding new values to enum types. Instead, extensions should use existing enum values and annotate additional semantic meaning in the `metadata` field.

These limitations exist to prevent extensions from breaking core type validations that clients and agents perform.

### Architecture Overview

TODO: A diagram outlining the components and their connections.

## Extension Declaration

Agents declare their support for extensions in their `AgentCard` by including `AgentExtension` objects in their `AgentCapabilities` object.

| Field Name    | Type      | Required | Description                                                                                 |
| :------------ | :-------- | :------- | :------------------------------------------------------------------------------------------ |
| `uri`         | `string`  | Yes      | The URI of the extension. This is an arbitrary identifier that the extension specification defines. Implementations of an extension use this URI to identify when to activate, and clients use this to determine extension compatibility. extension.                                                        |
| `required`    | `boolean` | No       | Whether the agent requires clients to use this extension. |
| `description` | `string`  | No       | A description of how the agent uses the declared extension. Full details of a extension are intended to be in an extension specification. This field is useful to explain the connection between the agent and the extension.                                    |
| `params`      | `object`  | No       | Extension-specific configuration. The expected values to be placed in this field, if any, are defined by the extension specification. This field can be used for specifying parameters of the extension or declaring additional agent-specific data.                                          |

An example `AgentCard` showing extensions:

```json
{
    "name": "Magic 8-ball",
    "description": "An agent that can tell your future... maybe.",
    "version": "0.1.0",
    "url": "https://example.com/agents/eightball",
    "capabilities": {
        "streaming": true,
        "extensions": [
            {
                "uri": "https://example.com/ext/konami-code/v1",
                "description": "Provide cheat codes to unlock new fortunes",
                "required": false,
                "params": {
                    "hints": [
                        "When your sims need extra cash fast",
                        "You might deny it, but we've seen the evidence of those cows."
                    ]
                }
            }
        ]
    },
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["text/plain"],
    "skills": [
        {
            "id": "fortune",
            "name": "Fortune teller",
            "description": "Seek advice from the mystical magic 8-ball",
            "tags": ["mystical", "untrustworthy"]
        }
    ]
}
```

### Required Extensions

While extensions are a means of enabling additional functionality, we anticipate that some agents will have stricter requirements than those expressible by the core A2A protocol. For example, an agent may require that all incoming messages are cryptographically signed by their author. Extensions that are declared `required` are intended to support this use case.

When an `AgentCard` declares a required extension, this is a signal to clients that some aspect of the extension impacts how requests are structured. Agents should not mark data-only extensions as required, since there is no direct impact on how requests are made to the agent.

If an `AgentCard` declares a required extension, and the client does not request activation of that required extension, Agents should return reject the incoming request and return an appropriate error code.

If a client requests extension activation, but does not follow an extension-defined protocol, the Agent should reject the request and return an appropriate validation failure message.

## Extension Specification

The details of an extension are defined by a specification. The exact format of this document is not specified, however it should contain at least:

- The specific URI(s) that extension implementations should identify and respond to. Multiple URIs may identify the same extension to account for versioning or changes in location of the specification document. Extension authors are encouraged to use a permanent identifier service, such as [w3id](https://w3id.org), to avoid a proliferation of URLs.

- The schema and meaning of objects specified in the `params` field of the `AgentExtension` object exposed in the `AgentCard`.

- The schemas of any additional data structures communicated between client and agent.

- Details of request/response flows, additional endpoints, or any other logic required to implement the extension.

### Extension Dependencies

Extensions may depend on other extensions. This dependency may be required, where the core functionality of the extension is unable to run without the presence of the dependent, or optional, where some additional functionality is enabled when another extension is present. Extension specifications should document the dependency and its type.

Dependencies are declared within the extension's specification, not in the `AgentExtension` object. It is the responsibility of the client to activate an extension *and* all of its required dependencies as listed in the extension's specification.

## Extension Activation

Extensions should default to being inactive. This provides a "default to baseline" experience, where extension-unaware clients are not burdened by the details and data provided by an extension. Instead, clients and agents perform negotiation to determine which extensions are active for a request. This negotiation is initiated by the client including the `X-A2A-Extensions` header in the HTTP request to the agent. The value of this header should be a list of extension URIs that the client is intending to activate.

Clients may request activation of any extension. Agents are responsible for identifying supported extensions in the request and performing the activation. Any requested extensions that are not supported by the agent can be ignored.

Not all extensions are activatable: data-only extensions exist solely to provide additional information via an AgentCard. Clients may still request activation of these extensions. Since the extension does not perform any additional logic upon activation, this should have no impact on the request.

Some extensions may have additional pre-requisites for activation. For example, some sensitive extensions may have a corresponding access-control list dictating who is allowed to activate the extension. It is up to the agent to determine which of the requested extensions are activated.

If a client requests activation of an extension with a required dependency, that client must also request activation of, and adhere to requirements of, that dependent extension. If the client does not request all required dependencies for a requested extension, the server may fail the request with an appropriate error.

Once the agent has identified all activated extensions, the response should include the `X-A2A-Extensions` header identifying all extensions that were activated.

An example request showing extension activation:

```HTTP
POST /agents/eightball HTTP/1.1
Host: example.com
Content-Type: application/json
X-A2A-Extensions: https://example.com/ext/konami-code/v1
Content-Length: 519

{
  "jsonrpc": "2.0",
  "method": "message/send",
  "id": "1",
  "params": {
    "message": {
        "kind": "message",
        "messageId": "1",
        "role": "user",
        "parts": [{"kind": "text", "text": "Oh magic 8-ball, will it rain today?"}]
    },
    "metadata": {
        "https://example.com/ext/konami-code/v1/code": "motherlode",
    }
  }
}
```

And corresponding response echoing the activated extensions:

```HTTP
HTTP/1.1 200 OK
Content-Type: application/json
X-A2A-Extensions: https://example.com/ext/konami-code/v1
Content-Length: 338

{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "kind": "message",
    "messageId": "2",
    "role": "agent",
    "parts": [{"kind": "text", "text": "That's a bingo!"}],
  }
}

```

## Implementation Considerations

While the A2A protocol defines the "what" of extensions, this section provides guidance on the "how"—best practices for authoring, versioning, and distributing extension implementations.

### Versioning

Extension specifications will inevitably evolve. It is crucial to have a clear versioning strategy to ensure that clients and agents can negotiate compatible implementations.

- **Recommendation**: Use the extension's URI as the primary version identifier. We recommend including a version number directly in the URI path, such as `https://example.com/ext/my-extension/v1` or `https://example.com/ext/my-extension/v2`.
- **Breaking Changes**: A new URI **MUST** be used when introducing a breaking change to an extension's logic, data structures, or required parameters. This prevents ambiguity and ensures that an agent supporting `/v1` does not incorrectly process a `/v2` request.
- **Handling Mismatches**: If a client requests a version of an extension that the agent does not support (e.g., client requests `/v2` but the agent only supports `/v1`), the agent **SHOULD** ignore the activation request for that extension. The agent **MUST NOT** attempt to "fall back" to a different version, as the client's logic is explicitly tied to the requested version.

### Discoverability and Publication

For an extension to be useful, other developers need to be able to find its specification and understand how to use it.

- **Specification Hosting**: The extension specification document **SHOULD** be hosted at the extension's URI. This allows developers to easily access the documentation by simply resolving the identifier.
- **Permanent Identifiers**: To prevent issues with broken links or changing domains, authors are encouraged to use a permanent identifier service, such as [w3id.org](https://w3id.org), for their extension URIs.
- **Community Registry (Future)**: In the future, the A2A community may establish a central registry for discovering and Browse available extensions.

### Packaging and Reusability

To promote adoption, extension logic should be packaged into reusable libraries that can be easily integrated into existing A2A client and server applications.

- **Distribution**: An extension implementation should be distributed as a standard package for its language ecosystem (e.g., a PyPI package for Python, an npm package for TypeScript/JavaScript).

- **Simplified Integration**: The goal should be a near "plug-and-play" experience for developers. A well-designed extension package should allow a developer to add it to their server with minimal code, for example:

    ```python
    # Hypothetical Python Server Integration
    from konami_code_extension import CheatCodeHandler
    from a2a.server import A2AServer, DefaultRequestHandler

    # The extension hooks into the request handler to process its logic
    extension = CheatCodeHandler(description="")
    extension.add_cheat(
        code="motherlode",
        hint="When your sims need extra cash fast",
    )
    extension.add_cheat(
        code="thereisnocowlevel",
        hint="You might deny it, but we've seen the evidence of those cows.",
    )
    request_handler = DefaultRequestHandler(
        agent_executor=MyAgentExecutor(extension),
        task_store=InMemoryTaskStore(),
        extensions=[extension]
    )

    server = A2AServer(agent_card, request_handler)
    server.run()
    ```

### Security

Extensions modify the core behavior of the A2A protocol and therefore introduce new security considerations.

- **Input Validation**: Any new data fields, parameters, or methods introduced by an extension **MUST** be rigorously validated by the implementation. Treat all extension-related data from an external party as untrusted input, unless there are protocol-defined means for establishing trust.
- **Scope of `required` extensions**: Be mindful when marking an extension as `required: true` in an `AgentCard`. This creates a hard dependency for all clients. Only use this for extensions that are fundamental to the agent's core function and security posture (e.g., a message signing extension).
- **Authentication and Authorization**: If an extension adds new methods, the implementation **MUST** ensure that these methods are subject to the same authentication and authorization checks as the core A2A methods. An extension **MUST NOT** provide a way to bypass the agent's primary security controls.
