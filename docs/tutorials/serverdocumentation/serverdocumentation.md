# OpenAPI Quickstart Tutorial: Documenting an A2A Server

Welcome to the Agent2Agent (A2A) Server Documentation Quickstart Tutorial!

In this tutorial, we will explore a standards based approach to document your implementation of the A2A protocol.

This hands-on guide will help you understand:

- The basic concepts behind the A2A protocol.
- Which standards can be used to document the A2A protocol.
- How you can describe each aspect of the A2A client/server interaction.

This is not a comprehensive guide to the A2A protocol, but rather a quickstart to help you get up and running with open specification standards.

The A2A protocol is designed to facilitate communication between agents in a standardized way, allowing them to share information and perform tasks collaboratively.

By using OpenRPC and OpenAPI, you can create a clear and structured documentation of your A2A implementation, making it easier for others to understand and integrate with your agent.

## Introduction

The [Agent2Agent (A2A) Protocol Specification](https://google.github.io/A2A/specification) is a set of standards that define how agents can communicate with each other in a structured and interoperable way. It allows agents to share information, request actions, and respond to queries in a consistent manner.
The protocol is designed to be flexible and extensible, enabling developers to create agents that can work together seamlessly.
The protocol uses HTTPS as the transport and JSON-RPC-2.0 as the message payload format. The payloads format are specified in the [protocol specification](https://google.github.io/A2A/specification). It is up to the implementer to document some details such as which authentication and authorization mechanisms are used, which interaction flows (send, sendSubscribe, notification,...) are available, which part types the agent supports or returns and other details.

Different parts of the protocol can be documented using different standard documentation. In this tutorial we will use OpenRPC, OpenAPI, and AsyncAPI standards.

### Interaction Flows covered in this tutorial

1. [**Agent discovery**](https://google.github.io/A2A/topics/agent-discovery/) - the specification specify [**Agent Cards**](https://google.github.io/A2A/specification/#5-agent-discovery-the-agent-card) as a digital "business card" for an A2A Server. You can register or distribute your agent card directly or you can register or distribute the domain or the Well-known URL of the agent card. We will cover the second method in this tutorial. The first method is not recommended because agent skills can evolve over time and the agent card may change, so it is better to register the Well-known URL in a registry or in the client host catalog.
2. [**tasks/send**](https://google.github.io/A2A/specification/#71-taskssend) - Sends a message to an agent to initiate a new task or to continue an existing one. This method is suitable for synchronous request/response interactions or when client-side polling (using tasks/get) is acceptable for monitoring longer-running tasks.
3. [**tasks/sendSubscribe**](https://google.github.io/A2A/specification/#72-tasksendsubscribe) - Sends a message to an agent to initiate/continue a task AND subscribes the client to real-time updates for that task via Server-Sent Events (SSE). This method requires the server to have AgentCard.capabilities.streaming: true.
4. [**tasks/get**](https://google.github.io/A2A/specification/#73-tasksget) - Retrieves the current state (including status, artifacts, and optionally history) of a previously initiated task. This is typically used for polling the status of a task initiated with tasks/send, or for fetching the final state of a task after being notified via a push notification or after an SSE stream has ended.
5. [**tasks/cancel**](https://google.github.io/A2A/specification/#74-taskscancel) - Requests the cancellation of an ongoing task. The server will attempt to cancel the task, but success is not guaranteed (e.g., the task might have already completed or failed, or cancellation might not be supported at its current stage).
6. [**tasks/pushNotification/set**](https://google.github.io/A2A/specification/#75-taskspushnotificationset) - Sets or updates the push notification configuration for a specified task. This allows the client to tell the server where and how to send asynchronous updates for the task. Requires the server to have AgentCard.capabilities.pushNotifications: true.
7. [**tasks/pushNotification/get**](https://google.github.io/A2A/specification/#76-taskspushnotificationsget) -  Retrieves the current push notification configuration for a specified task. Requires the server to have AgentCard.capabilities.pushNotifications: true.
8. [**tasks/resubscribe**](https://google.github.io/A2A/specification/#77-tasksresubscribe) - Allows a client to reconnect to an SSE stream for an ongoing task after a previous connection (from tasks/sendSubscribe or an earlier tasks/resubscribe) was interrupted. Requires the server to have AgentCard.capabilities.streaming: true.

### Standards used in this tutorial

- **[OpenRPC](https://open-rpc.org/)**: A specification for describing JSON-RPC APIs. It provides a way to document the methods, parameters, and responses of your A2A server.
- **[OpenAPI](https://www.openapis.org/)**: A specification for describing RESTful APIs. It is used to document the HTTP endpoints of your A2A server, including authentication and authorization mechanisms.

## Getting Started

### Well-Known URI

This is a recommended approach for public agents or agents intended for broad discoverability within a specific domain.
The specification determines the standard Path: https://{agent-server-domain}/.well-known/agent.json, following the principles of the [Well-Known URI](https://www.ietf.org/rfc/rfc8615.txt) specification.
This is a simple GET request that returns the agent card in JSON format.
Because the agent card dynamic nature, sometimes it is worth documenting it with OpenAPI, so that the client can discover the agent card and its capabilities but it is not required (one can simple publish the agent domain).
Here is a sample OpenAPI document that describes the agent card endpoint:

```yaml
openapi: 3.1.0
info:
  title: Agent-to-Agent AgentCard Discovery
  version: 1.0.0
  description: >
    Specification for serving an AgentCard at the well-known endpoint
    /.well-known/agent.json according to the A2A protocol.
    The AgentCard conveys key information about an A2A Server including its identity,
    service endpoints, capabilities, authentication requirements, and skills.

servers:
  - url: https://{server_domain}
    variables:
      server_domain:
        default: example.com
        description: The domain where the agent is hosted

paths:
  /.well-known/agent.json:
    get:
      summary: Retrieve AgentCard
      description: >
        Returns the AgentCard describing the agent's capabilities, skills,
        and authentication requirements. The AgentCard serves as the primary
        discovery mechanism for agents in the A2A ecosystem.
      operationId: getAgentCard
      responses:
        '200':
          description: AgentCard retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AgentCard'
              example:
                name: "Recipe Advisor Agent"
                description: "Helps users find recipes and plan meals"
                url: "https://agent.example.com/a2a/api"
                version: "1.0.0"
                capabilities:
                  streaming: true
                  pushNotifications: false
                skills:
                  - id: "recipe-finder"
                    name: "Recipe Finder"
                    description: "Finds recipes based on ingredients and dietary restrictions"
        '401':
          description: Unauthorized - Authentication failed or was not provided
        '403':
          description: Forbidden - Client lacks permission to access the AgentCard
        '500':
          description: Server error - Unexpected condition prevented fulfilling the request

      security:
        - BearerAuth: []
        - OAuth2: []
        - ApiKeyAuth: []
        - BasicAuth: []
      tags:
        - Discovery

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: Standard JWT Bearer Token authentication
    BasicAuth:
      type: http
      scheme: basic
      description: Basic HTTP authentication (username/password)
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
      description: API key authentication via custom header
    OAuth2:
      type: oauth2
      description: OAuth2 authentication using authorization code flow
      flows:
        authorizationCode:
          authorizationUrl: https://example.com/oauth/authorize
          tokenUrl: https://example.com/oauth/token
          scopes:
            read: Read access to the agent
            write: Write access to the agent

  schemas:
    AgentCard:
      type: object
      description: >
        Conveys key information about an A2A Server including its identity,
        service endpoints, capabilities, authentication requirements, and skills.
      required: [name, url, version, capabilities, skills]
      properties:
        name:
          type: string
          description: Human-readable name of the agent (e.g., "Recipe Advisor Agent")
          example: "Recipe Advisor Agent"
        description:
          type: string
          nullable: true
          description: >
            Human-readable description of the agent and its purpose.
            CommonMark MAY be used for rich text formatting.
          example: "This agent helps users find recipes, plan meals, and get cooking instructions."
        url:
          type: string
          format: uri
          description: >
            The base URL endpoint for the agent's A2A service.
            Must be an absolute HTTPS URL for production.
          example: "https://agent.example.com/a2a/api"
        provider:
          $ref: '#/components/schemas/AgentProvider'
          description: Information about the organization or entity providing the agent
        version:
          type: string
          description: >
            Version string for the agent or its A2A implementation.
            Format is defined by the provider (e.g., "1.0.0", "2023-10-26-beta").
          example: "1.0.0"
        documentationUrl:
          type: string
          format: uri
          nullable: true
          description: URL pointing to human-readable documentation for the agent
          example: "https://agent.example.com/docs"
        capabilities:
          $ref: '#/components/schemas/AgentCapabilities'
          description: Specifies optional A2A protocol features supported by this agent
        authentication:
          $ref: '#/components/schemas/AgentAuthentication'
          description: >
            Authentication schemes required to interact with the agent's endpoint.
            If null or omitted, no A2A-level authentication is explicitly advertised.
        defaultInputModes:
          type: array
          items:
            type: string
          description: >
            Array of MIME types the agent generally accepts as input across all skills,
            unless overridden by a specific skill. Defaults to ["text/plain"] if omitted.
          example: ["text/plain", "application/json"]
        defaultOutputModes:
          type: array
          items:
            type: string
          description: >
            Array of MIME types the agent generally produces as output across all skills,
            unless overridden by a specific skill. Defaults to ["text/plain"] if omitted.
          example: ["text/plain", "application/json"]
        skills:
          type: array
          items:
            $ref: '#/components/schemas/AgentSkill'
          description: >
            An array of specific skills or capabilities the agent offers.
            Must contain at least one skill if the agent is expected to perform actions.

    AgentProvider:
      type: object
      description: Information about the organization or entity providing the agent
      required: [organization]
      properties:
        organization:
          type: string
          description: Name of the organization or entity
          example: "Example Corp"
        url:
          type: string
          format: uri
          nullable: true
          description: URL for the provider's organization website or relevant contact page
          example: "https://example.com"

    AgentCapabilities:
      type: object
      description: Specifies optional A2A protocol features supported by the agent
      properties:
        streaming:
          type: boolean
          default: false
          description: >
            If true, the agent supports tasks/sendSubscribe and tasks/resubscribe
            for real-time updates via Server-Sent Events (SSE).
        pushNotifications:
          type: boolean
          default: false
          description: >
            If true, the agent supports tasks/pushNotification/set and tasks/pushNotification/get
            for asynchronous task updates via webhooks.
        stateTransitionHistory:
          type: boolean
          default: false
          description: >
            Placeholder for future feature: exposing detailed task status change history.

    AgentAuthentication:
      type: object
      description: Describes the authentication requirements for accessing the agent's endpoint
      required: [schemes]
      properties:
        schemes:
          type: array
          items:
            type: string
          description: >
            Array of authentication scheme names supported/required by the agent's endpoint
            (e.g., "Bearer", "Basic", "OAuth2", "ApiKey").
          example: ["Bearer", "OAuth2"]
        credentials:
          type: string
          nullable: true
          description: >
            Optional non-secret, scheme-specific information.
            MUST NOT contain plaintext secrets (e.g., actual API key values, passwords).

    AgentSkill:
      type: object
      description: Describes a specific capability or function the agent can perform
      required: [id, name]
      properties:
        id:
          type: string
          description: >
            Unique identifier for this skill within the context of this agent
            (e.g., "currency-converter", "generate-image-from-prompt").
          example: "recipe-finder"
        name:
          type: string
          description: Human-readable name of the skill
          example: "Recipe Finder"
        description:
          type: string
          nullable: true
          description: >
            Detailed description of what the skill does. CommonMark MAY be used for rich text.
          example: "Finds recipes based on ingredients and dietary restrictions"
        tags:
          type: array
          items:
            type: string
          nullable: true
          description: Array of keywords or categories for discoverability
          example: ["food", "cooking", "recipes"]
        examples:
          type: array
          items:
            type: string
          nullable: true
          description: Array of example prompts illustrating how to use this skill
          example: ["Find vegetarian pasta recipes", "Show me quick 30-minute meals"]
        inputModes:
          type: array
          items:
            type: string
          nullable: true
          description: >
            Overrides defaultInputModes for this specific skill. Accepted MIME types.
          example: ["text/plain", "application/json"]
        outputModes:
          type: array
          items:
            type: string
          nullable: true
          description: >
            Overrides defaultOutputModes for this specific skill. Produced MIME types.
          example: ["text/plain", "application/json"]
```

- Notes:

  1. The security field under paths allows the endpoint to be protected by one or more specified security schemes. In real-world scenarios, it's best practice to select a minimal set of authentication mechanisms—typically one—that align with your system's security and interoperability requirements. Supporting too many schemes simultaneously can unnecessarily increase the attack surface, add operational complexity, and create inconsistent access control behavior across clients.

  2. In this example for the sake of simplicity, we didn't specify any scope for the security schemes. You can specify according to your needs. For example, you can specify scopes for read and write access to the agent, or any other scopes that are relevant to your implementation.

  3. Clients can still inspect the authentication.schemes in the AgentCard payload to determine which schemes apply dynamically for the agents methods. Remember that this OpenAPI is specific to the agent card endpoint and does not cover the methods of the agent.

This OpenAPI document provides a structured way to describe the agent card endpoint, including its purpose, responses, security requirements, and the structure of the AgentCard itself. It serves as a useful reference for clients interacting with the A2A protocol. But, in other words, this endpoint is a simple GET request that returns the agent card in JSON format, and it is not required to be documented with OpenAPI. The agent card can be distributed or registered in a registry or in the client host catalog.

### A2A Client/Server Interaction Methods

All agent-to-agent (A2A) client/server interaction methods are documented using OpenRPC. OpenRPC is a specification for describing JSON-RPC APIs, which is the message format used in the A2A protocol.
Note that the security aspects of the A2A protocol are not covered by OpenRPC. The OpenRPC specification focuses on the methods, parameters, and responses of the A2A server. The security aspects, such as authentication and authorization, are typically documented in the agent card.
Also note that this OpenRPC specification  is not exhaustive but tries to cover the most common use cases of the A2A protocol. A real agent service does not have to implement all of these methods but it needs to implements methods according to the AgentCapabilities specified in its agent card.

```json
{
  "openrpc": "1.3.2",
  "info": {
    "version": "1.0.0",
    "title": "Petstore",
    "license": {
      "name": "MIT"
    },
    "description": "Transport Protocol\nAll A2A RPC methods are invoked via HTTP POST to the A2A Server's endpoint (specified in its AgentCard).\n- Request body MUST be a JSONRPCRequest object\n- Request Content-Type MUST be application/json\n- Response body MUST be a JSONRPCResponse object (or SSE stream for streaming methods)\n- Response Content-Type is application/json (or text/event-stream for SSE)"
  },
  "servers": [
    {
      "name": "A2A Server",
      "url": "https://{a2aServerUrl}",
      "description": "Base URL should be obtained from the AgentCard.url field",
      "variables": {
        "a2aServerUrl": {
          "description": "The A2A Server's endpoint URL as specified in its AgentCard",
          "default": "agent.example.com"
        }
      },
      "x-transport": {
        "protocol": "https",
        "methods": {
          "default": {
            "httpMethod": "POST",
            "requestContentType": "application/json",
            "responseContentType": "application/json"
          },
          "streaming": {
            "httpMethod": "POST",
            "requestContentType": "application/json",
            "responseContentType": "text/event-stream",
            "description": "For methods that support streaming"
          }
        }
      }
    }
  ],
  "methods": [
    {
      "name": "tasks/send",
      "summary": "Send a message to initiate or continue a task",
      "description": "Sends a message to an agent to initiate a new task or to continue an existing one. This method is suitable for synchronous request/response interactions or when client-side polling (using tasks/get) is acceptable for monitoring longer-running tasks.",
      "params": [
        {
          "name": "id",
          "description": "Task ID. If new, the server SHOULD create the task. If existing, this message continues the task.",
          "required": true,
          "schema": {
            "type": "string"
          }
        },
        {
          "name": "sessionId",
          "description": "Optional client-generated session ID to group this task with others.",
          "required": false,
          "schema": {
            "type": "string",
            "nullable": true
          }
        },
        {
          "name": "message",
          "description": "The message content to send. Message.role is typically 'user'.",
          "required": true,
          "schema": {
            "$ref": "#/components/schemas/Message"
          }
        },
        {
          "name": "pushNotification",
          "description": "Optional: sets push notification configuration for the task (usually on the first send). Requires server capability.",
          "required": false,
          "schema": {
            "$ref": "#/components/schemas/PushNotificationConfig",
            "nullable": true
          }
        },
        {
          "name": "historyLength",
          "description": "If positive, requests the server to include up to N recent messages in Task.history.",
          "required": false,
          "schema": {
            "type": "integer",
            "nullable": true
          }
        },
        {
          "name": "metadata",
          "description": "Request-specific metadata.",
          "required": false,
          "schema": {
            "type": "object",
            "additionalProperties": true,
            "nullable": true
          }
        }
      ],
      "result": {
        "name": "task",
        "description": "The current or final state of the task after processing the message.",
        "schema": {
          "$ref": "#/components/schemas/Task"
        }
      },
      "errors": [
        {
          "$ref": "#/components/errors/InvalidParams"
        },
        {
          "$ref": "#/components/errors/TaskNotFound"
        },
        {
          "$ref": "#/components/errors/PermissionDenied"
        }
      ]
    },
    {
      "name": "tasks/sendSubscribe",
      "summary": "Send a message to initiate/continue a task and subscribe to real-time updates",
      "description": "Sends a message to an agent to initiate/continue a task AND subscribes the client to real-time updates for that task via Server-Sent Events (SSE). This method requires the server to have AgentCard.capabilities.streaming: true.",
      "x-transport": "streaming",
      "params": [
        {
          "name": "id",
          "description": "Task ID. If new, the server SHOULD create the task. If existing, this message continues the task.",
          "required": true,
          "schema": {
            "type": "string"
          }
        },
        {
          "name": "sessionId",
          "description": "Optional client-generated session ID to group this task with others.",
          "required": false,
          "schema": {
            "type": "string",
            "nullable": true
          }
        },
        {
          "name": "message",
          "description": "The message content to send. Message.role is typically 'user'.",
          "required": true,
          "schema": {
            "$ref": "#/components/schemas/Message"
          }
        },
        {
          "name": "pushNotification",
          "description": "Optional: sets push notification configuration for the task (usually on the first send). Requires server capability.",
          "required": false,
          "schema": {
            "$ref": "#/components/schemas/PushNotificationConfig",
            "nullable": true
          }
        },
        {
          "name": "historyLength",
          "description": "If positive, requests the server to include up to N recent messages in Task.history.",
          "required": false,
          "schema": {
            "type": "integer",
            "nullable": true
          }
        },
        {
          "name": "metadata",
          "description": "Request-specific metadata.",
          "required": false,
          "schema": {
            "type": "object",
            "additionalProperties": true,
            "nullable": true
          }
        }
      ],
      "result": {
        "name": "stream",
        "description": "A stream of Server-Sent Events. Each SSE data field contains a SendTaskStreamingResponse JSON object.",
        "schema": {
          "$ref": "#/components/schemas/SendTaskStreamingResponse"
        }
      },
      "errors": [
        {
          "$ref": "#/components/errors/InvalidParams"
        },
        {
          "$ref": "#/components/errors/TaskNotFound"
        },
        {
          "$ref": "#/components/errors/PermissionDenied"
        },
        {
          "$ref": "#/components/errors/StreamingNotSupported"
        }
      ]
    },
    {
      "name": "tasks/get",
      "summary": "Retrieve the current state of a task",
      "description": "Retrieves the current state (including status, artifacts, and optionally history) of a previously initiated task. This is typically used for polling the status of a task initiated with tasks/send, or for fetching the final state of a task after being notified via a push notification or after an SSE stream has ended.",
      "params": [
        {
          "name": "id",
          "description": "The ID of the task to retrieve.",
          "required": true,
          "schema": {
            "type": "string"
          }
        },
        {
          "name": "historyLength",
          "description": "If positive, requests the server to include up to N recent messages in Task.history.",
          "required": false,
          "schema": {
            "type": "integer",
            "nullable": true
          }
        },
        {
          "name": "metadata",
          "description": "Request-specific metadata.",
          "required": false,
          "schema": {
            "type": "object",
            "additionalProperties": true,
            "nullable": true
          }
        }
      ],
      "result": {
        "name": "task",
        "description": "A snapshot of the task's current state.",
        "schema": {
          "$ref": "#/components/schemas/Task"
        }
      },
      "errors": [
        {
          "$ref": "#/components/errors/InvalidParams"
        },
        {
          "$ref": "#/components/errors/TaskNotFound"
        },
        {
          "$ref": "#/components/errors/PermissionDenied"
        }
      ]
    },
    {
      "name": "tasks/cancel",
      "summary": "Request cancellation of an ongoing task",
      "description": "Requests the cancellation of an ongoing task. The server will attempt to cancel the task, but success is not guaranteed (e.g., the task might have already completed or failed, or cancellation might not be supported at its current stage).",
      "params": [
        {
          "name": "id",
          "description": "The ID of the task to cancel.",
          "required": true,
          "schema": {
            "type": "string"
          }
        },
        {
          "name": "metadata",
          "description": "Request-specific metadata.",
          "required": false,
          "schema": {
            "type": "object",
            "additionalProperties": true,
            "nullable": true
          }
        }
      ],
      "result": {
        "name": "task",
        "description": "The state of the task after the cancellation attempt.",
        "schema": {
          "$ref": "#/components/schemas/Task"
        }
      },
      "errors": [
        {
          "$ref": "#/components/errors/InvalidParams"
        },
        {
          "$ref": "#/components/errors/TaskNotFound"
        },
        {
          "$ref": "#/components/errors/PermissionDenied"
        },
        {
          "code": 400,
          "message": "Task not cancelable"
        }
      ]
    },
    {
      "name": "tasks/pushNotification/set",
      "summary": "Set push notification configuration for a task",
      "description": "Sets or updates the push notification configuration for a specified task. This allows the client to tell the server where and how to send asynchronous updates for the task.",
      "params": [
        {
          "name": "id",
          "description": "The ID of the task to configure.",
          "required": true,
          "schema": {
            "type": "string"
          }
        },
        {
          "name": "pushNotificationConfig",
          "description": "The push notification configuration.",
          "required": true,
          "schema": {
            "$ref": "#/components/schemas/PushNotificationConfig",
            "nullable": true
          }
        }
      ],
      "result": {
        "name": "config",
        "description": "Confirms the configuration that was set.",
        "schema": {
          "$ref": "#/components/schemas/TaskPushNotificationConfig"
        }
      },
      "errors": [
        {
          "$ref": "#/components/errors/InvalidParams"
        },
        {
          "$ref": "#/components/errors/TaskNotFound"
        },
        {
          "$ref": "#/components/errors/PermissionDenied"
        },
        {
          "code": 501,
          "message": "Push notifications not supported"
        }
      ]
    },
    {
      "name": "tasks/pushNotification/get",
      "summary": "Get push notification configuration for a task",
      "description": "Retrieves the current push notification configuration for a specified task.",
      "params": [
        {
          "name": "id",
          "description": "The ID of the task to query.",
          "required": true,
          "schema": {
            "type": "string"
          }
        },
        {
          "name": "metadata",
          "description": "Request-specific metadata.",
          "required": false,
          "schema": {
            "type": "object",
            "additionalProperties": true,
            "nullable": true
          }
        }
      ],
      "result": {
        "name": "config",
        "description": "The current push notification configuration for the task.",
        "schema": {
          "$ref": "#/components/schemas/TaskPushNotificationConfig"
        }
      },
      "errors": [
        {
          "$ref": "#/components/errors/InvalidParams"
        },
        {
          "$ref": "#/components/errors/TaskNotFound"
        },
        {
          "$ref": "#/components/errors/PermissionDenied"
        },
        {
          "code": 501,
          "message": "Push notifications not supported"
        }
      ]
    },
    {
      "name": "tasks/resubscribe",
      "summary": "Resubscribe to a task's SSE stream",
      "description": "Allows a client to reconnect to an SSE stream for an ongoing task after a previous connection was interrupted.",
      "x-transport": "streaming",
      "params": [
        {
          "name": "id",
          "description": "The ID of the task to resubscribe to.",
          "required": true,
          "schema": {
            "type": "string"
          }
        },
        {
          "name": "historyLength",
          "description": "Typically ignored for resubscription, but included for structural consistency.",
          "required": false,
          "schema": {
            "type": "integer",
            "nullable": true
          }
        },
        {
          "name": "metadata",
          "description": "Request-specific metadata.",
          "required": false,
          "schema": {
            "type": "object",
            "additionalProperties": true,
            "nullable": true
          }
        }
      ],
      "result": {
        "name": "stream",
        "description": "A stream of Server-Sent Events with subsequent updates for the task.",
        "schema": {
          "$ref": "#/components/schemas/SendTaskStreamingResponse"
        }
      },
      "errors": [
        {
          "$ref": "#/components/errors/InvalidParams"
        },
        {
          "$ref": "#/components/errors/TaskNotFound"
        },
        {
          "$ref": "#/components/errors/PermissionDenied"
        },
        {
          "$ref": "#/components/errors/StreamingNotSupported"
        }
      ]
    }
  ],
  "components": {
    "schemas": {
      "Task": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "description": "A unique identifier for the task (e.g., a UUID v4)"
          },
          "sessionId": {
            "type": "string",
            "nullable": true,
            "description": "Optional client-generated identifier to group related tasks"
          },
          "status": {
            "$ref": "#/components/schemas/TaskStatus"
          },
          "artifacts": {
            "type": "array",
            "items": {
              "$ref": "#/components/schemas/Artifact"
            },
            "nullable": true
          },
          "history": {
            "type": "array",
            "items": {
              "$ref": "#/components/schemas/Message"
            },
            "nullable": true
          },
          "metadata": {
            "type": "object",
            "additionalProperties": true,
            "nullable": true
          }
        },
        "required": ["id", "status"]
      },
      "TaskStatus": {
        "type": "object",
        "properties": {
          "state": {
            "$ref": "#/components/schemas/TaskState"
          },
          "message": {
            "$ref": "#/components/schemas/Message",
            "nullable": true
          },
          "timestamp": {
            "type": "string",
            "format": "date-time",
            "nullable": true
          }
        },
        "required": ["state"]
      },
      "TaskState": {
        "type": "string",
        "enum": ["submitted", "working", "input-required", "completed", "canceled", "failed", "unknown"]
      },
      "Message": {
        "type": "object",
        "properties": {
          "role": {
            "type": "string",
            "enum": ["user", "agent"]
          },
          "parts": {
            "type": "array",
            "items": {
              "$ref": "#/components/schemas/Part"
            },
            "minItems": 1
          },
          "metadata": {
            "type": "object",
            "additionalProperties": true,
            "nullable": true
          }
        },
        "required": ["role", "parts"]
      },
      "Part": {
        "oneOf": [
          {
            "$ref": "#/components/schemas/TextPart"
          },
          {
            "$ref": "#/components/schemas/FilePart"
          },
          {
            "$ref": "#/components/schemas/DataPart"
          }
        ]
      },
      "TextPart": {
        "type": "object",
        "properties": {
          "type": {
            "type": "string",
            "const": "text"
          },
          "text": {
            "type": "string"
          },
          "metadata": {
            "type": "object",
            "additionalProperties": true,
            "nullable": true
          }
        },
        "required": ["type", "text"]
      },
      "FilePart": {
        "type": "object",
        "properties": {
          "type": {
            "type": "string",
            "const": "file"
          },
          "file": {
            "$ref": "#/components/schemas/FileContent"
          },
          "metadata": {
            "type": "object",
            "additionalProperties": true,
            "nullable": true
          }
        },
        "required": ["type", "file"]
      },
      "DataPart": {
        "type": "object",
        "properties": {
          "type": {
            "type": "string",
            "const": "data"
          },
          "data": {
            "type": ["object", "array"]
          },
          "metadata": {
            "type": "object",
            "additionalProperties": true,
            "nullable": true
          }
        },
        "required": ["type", "data"]
      },
      "FileContent": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string",
            "nullable": true
          },
          "mimeType": {
            "type": "string",
            "nullable": true
          },
          "bytes": {
            "type": "string",
            "nullable": true
          },
          "uri": {
            "type": "string",
            "nullable": true
          }
        }
      },
      "Artifact": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string",
            "nullable": true
          },
          "description": {
            "type": "string",
            "nullable": true
          },
          "parts": {
            "type": "array",
            "items": {
              "$ref": "#/components/schemas/Part"
            },
            "minItems": 1
          },
          "index": {
            "type": "integer",
            "minimum": 0,
            "default": 0
          },
          "append": {
            "type": "boolean",
            "nullable": true,
            "default": false
          },
          "lastChunk": {
            "type": "boolean",
            "nullable": true,
            "default": false
          },
          "metadata": {
            "type": "object",
            "additionalProperties": true,
            "nullable": true
          }
        },
        "required": ["parts"]
      },
      "PushNotificationConfig": {
        "type": "object",
        "properties": {
          "url": {
            "type": "string",
            "description": "Absolute HTTPS webhook URL for the A2A Server to POST task updates to.",
            "format": "uri",
            "pattern": "^https://"
          },
          "token": {
            "type": "string",
            "description": "Optional client-generated opaque token for the client's webhook receiver to validate the notification (e.g., server includes it in X-A2A-Notification-Token header).",
            "nullable": true
          },
          "authentication": {
            "$ref": "#/components/schemas/AuthenticationInfo",
            "nullable": true,
            "description": "Authentication details the A2A Server must use when calling the url. The client's webhook (receiver) defines these requirements."
          }
        },
        "required": ["url"],
        "description": "Configuration provided by the client to the server for sending asynchronous push notifications about task updates."
      },
      "AuthenticationInfo": {
        "type": "object",
        "properties": {
          "schemes": {
            "type": "array",
            "items": {
              "type": "string",
              "examples": ["Bearer", "ApiKey", "Basic"]
            },
            "description": "Array of authentication scheme names the caller must use when sending the request to the webhook URL."
          },
          "credentials": {
            "type": "string",
            "nullable": true,
            "description": "Optional static credentials or scheme-specific configuration info. Handle with EXTREME CAUTION if secrets are involved. Prefer server-side dynamic credential fetching where possible."
          }
        },
        "required": ["schemes"],
        "description": "A generic structure for specifying authentication requirements, typically used within PushNotificationConfig."
      },
      "TaskPushNotificationConfig": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "description": "The ID of the task to configure push notifications for, or retrieve configuration from."
          },
          "pushNotificationConfig": {
            "$ref": "#/components/schemas/PushNotificationConfig",
            "nullable": true,
            "description": "The push notification configuration. For set, the desired config. For get, the current config (secrets MAY be omitted by server). null might clear config on set."
          }
        },
        "required": ["id", "pushNotificationConfig"],
        "description": "Used as the params object for the tasks/pushNotification/set method and as the result object for the tasks/pushNotification/get method."
      },
      "SendTaskStreamingResponse": {
        "type": "object",
        "properties": {
          "jsonrpc": {
            "type": "string",
            "const": "2.0"
          },
          "id": {
            "type": ["string", "number"],
            "description": "Matches the id from the originating tasks/sendSubscribe or tasks/resubscribe request."
          },
          "result": {
            "oneOf": [
              {
                "$ref": "#/components/schemas/TaskStatusUpdateEvent"
              },
              {
                "$ref": "#/components/schemas/TaskArtifactUpdateEvent"
              }
            ],
            "description": "The event payload: either a status update or an artifact update."
          },
          "error": {
            "$ref": "#/components/schemas/JSONRPCError",
            "nullable": true,
            "description": "Typically null or absent for stream events. If a fatal stream error occurs, this MAY be populated in the final SSE message before the stream closes."
          }
        },
        "required": ["jsonrpc", "id", "result"],
        "description": "The structure of the JSON object found in the data field of each Server-Sent Event sent by the server for a tasks/sendSubscribe or tasks/resubscribe stream."
      },
      "TaskStatusUpdateEvent": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "description": "Task ID being updated, matching the original request's task ID."
          },
          "status": {
            "$ref": "#/components/schemas/TaskStatus",
            "description": "The new TaskStatus object."
          },
          "final": {
            "type": "boolean",
            "default": false,
            "description": "If true, indicates this is the terminal status update for the current stream cycle. The server typically closes the SSE connection after this."
          },
          "metadata": {
            "type": "object",
            "additionalProperties": true,
            "nullable": true,
            "description": "Event-specific metadata."
          }
        },
        "required": ["id", "status"],
        "description": "Carries information about a change in the task's status during streaming."
      },
      "TaskArtifactUpdateEvent": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "description": "Task ID that generated the artifact, matching the original request's task ID."
          },
          "artifact": {
            "$ref": "#/components/schemas/Artifact",
            "description": "The Artifact data. Could be a complete artifact or an incremental chunk. Use index, append, and lastChunk fields within Artifact for client-side assembly."
          },
          "metadata": {
            "type": "object",
            "additionalProperties": true,
            "nullable": true,
            "description": "Event-specific metadata."
          }
        },
        "required": ["id", "artifact"],
        "description": "Carries a new or updated artifact (or a chunk of an artifact) generated by the task during streaming."
      },
      "JSONRPCError": {
        "type": "object",
        "properties": {
          "code": {
            "type": "integer",
            "description": "A Number that indicates the error type that occurred."
          },
          "message": {
            "type": "string",
            "description": "A short description of the error."
          },
          "data": {
            "type": ["object", "array", "string", "number", "boolean", "null"],
            "description": "Additional information about the error."
          }
        },
        "required": ["code", "message"],
        "description": "Defines the application level error."
      }
    },
    "errors": {
      "InvalidParams": {
        "code": -32602,
        "message": "Invalid parameters"
      },
      "TaskNotFound": {
        "code": 404,
        "message": "Task not found"
      },
      "PermissionDenied": {
        "code": 403,
        "message": "Permission denied"
      },
      "StreamingNotSupported": {
        "code": 501,
        "message": "Streaming not supported by this agent"
      },
      "TaskNotCancelable": {
        "code": 400,
        "message": "Task not cancelable"
      },
      "PushNotificationNotSupported": {
        "code": 501,
        "message": "Push notifications not supported"
      }
    }
  }
}
```
