# A2A Models (Go)

This package contains the data structures for the Agent-to-Agent (A2A) communication protocol.

## Overview

The models package provides type-safe structures for:
- JSON-RPC 2.0 messages
- Agent metadata and capabilities
- Task management
- Error handling

## Core Types

### JSON-RPC Types

- `JSONRPCMessage`: Base interface for all JSON-RPC messages
- `JSONRPCMessageIdentifier`: Interface for identifying JSON-RPC messages
- `JSONRPCRequest`: Request object structure
- `JSONRPCResponse`: Response object structure
- `JSONRPCError`: Error object structure

### Agent Types

- `AgentCard`: Agent metadata card
- `AgentProvider`: Provider information
- `AgentCapabilities`: Agent capabilities
- `AgentSkill`: Agent skill definition
- `AgentAuthentication`: Authentication details

### Task Types

- `Task`: Task representation
- `TaskStatus`: Task status information
- `TaskState`: Task state enumeration
- `Message`: Message content
- `Part`: Message part (text, file, data)
- `Artifact`: Task output artifact

### Request/Response Types

- `TaskSendParams`: Parameters for sending a task
- `TaskQueryParams`: Parameters for querying a task
- `TaskIDParams`: Parameters for task ID-based operations
- `PushNotificationConfig`: Push notification configuration

## Usage

```go
package main

import (
    "a2a/models"
)

func main() {
    // Create a task message
    message := models.Message{
        Role: "user",
        Parts: []models.Part{
            {
                Type: stringPtr("text"),
                Text: stringPtr("Hello, A2A agent!"),
            },
        },
    }

    // Create task parameters
    params := models.TaskSendParams{
        ID:      "task-1",
        Message: message,
    }

    // Use the parameters...
}
```

## Error Codes

The package defines standard error codes for the A2A protocol:

- `ErrorCodeParseError`: Invalid JSON
- `ErrorCodeInvalidRequest`: Invalid request format
- `ErrorCodeMethodNotFound`: Method not found
- `ErrorCodeInvalidParams`: Invalid parameters
- `ErrorCodeInternalError`: Internal server error
- `ErrorCodeTaskNotFound`: Task not found
- `ErrorCodeTaskAlreadyExists`: Task already exists
- `ErrorCodeTaskInProgress`: Task in progress
- `ErrorCodeTaskCompleted`: Task already completed
- `ErrorCodeTaskCanceled`: Task already canceled
- `ErrorCodeTaskFailed`: Task already failed
- `ErrorCodeInvalidTaskState`: Invalid task state transition
- `ErrorCodeInvalidTaskID`: Invalid task ID
- `ErrorCodeInvalidMessage`: Invalid message format
- `ErrorCodeInvalidPart`: Invalid message part
- `ErrorCodeInvalidArtifact`: Invalid artifact format
- `ErrorCodeInvalidFileContent`: Invalid file content
- `ErrorCodeInvalidURI`: Invalid URI format
- `ErrorCodeInvalidAuthentication`: Invalid authentication
- `ErrorCodeAuthenticationRequired`: Authentication required
- `ErrorCodeAuthenticationFailed`: Authentication failed
- `ErrorCodeRateLimitExceeded`: Rate limit exceeded
- `ErrorCodeQuotaExceeded`: Quota exceeded
- `ErrorCodeServiceUnavailable`: Service unavailable
- `ErrorCodeTimeout`: Request timeout
- `ErrorCodeConnectionError`: Connection error
- `ErrorCodeProtocolError`: Protocol error
- `ErrorCodeUnknownError`: Unknown error

## Testing

Run the tests with:

```bash
go test ./...
```

The test suite verifies:
- JSON serialization/deserialization
- Type validation
- Error handling
- Task state transitions 