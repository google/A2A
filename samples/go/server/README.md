# A2A Server (Go)

This directory contains a Go server implementation for the Agent-to-Agent (A2A) communication protocol.

## Features

- JSON-RPC 2.0 compliant server
- Supports core A2A methods:
  - `tasks/send`: Send a new task
  - `tasks/get`: Get task status
  - `tasks/cancel`: Cancel a task
- Streaming task updates with Server-Sent Events (SSE)
- Thread-safe task storage
- Task history tracking
- Error handling with A2A error codes

## Usage

```go
package main

import (
    "log"
    "a2a/samples/go/server"
    "a2a/samples/go/models"
)

// Example task handler
func taskHandler(task *models.Task, message *models.Message) (*models.Task, error) {
    // Process the task
    task.Status.State = "completed"
    return task, nil
}

func main() {
    // Create a new server instance
    srv := server.NewA2AServer(taskHandler, 8080, "/")
    
    // Start the server
    log.Fatal(srv.Start())
}
```

## API

### NewA2AServer

```go
func NewA2AServer(handler TaskHandler, port int, basePath string) *A2AServer
```

Creates a new A2A server instance with the specified task handler, port, and base path.

### TaskHandler

```go
type TaskHandler func(task *models.Task, message *models.Message) (*models.Task, error)
```

A function type that handles task processing. It receives a task and message, and returns an updated task or an error.

### A2AServer Methods

#### Start

```go
func (s *A2AServer) Start() error
```

Starts the HTTP server on the configured port.

## Streaming Support

The server supports streaming task updates using Server-Sent Events (SSE). To use streaming:

1. Set the `Accept` header to `text/event-stream` in your request
2. The server will respond with a stream of task status updates
3. Each update will be a JSON object containing:
   - Task ID
   - Current status
   - Whether it's the final update

Example streaming response:
```json
{"result":{"id":"task-1","status":{"state":"working"},"final":false}}
{"result":{"id":"task-1","status":{"state":"completed"},"final":true}}
```

## Testing

Run the tests with:

```bash
go test ./...
```

The test suite includes examples of:
- Sending tasks
- Getting task status
- Canceling tasks
- Streaming task updates
- Error handling 