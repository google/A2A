# A2A Client (Go)

This package provides a Go client implementation for the Agent-to-Agent (A2A) communication protocol.

## Features

- JSON-RPC 2.0 compliant client
- Supports core A2A methods:
  - `tasks/send`: Send a new task
  - `tasks/get`: Get task status
  - `tasks/cancel`: Cancel a task
- Streaming task updates with Server-Sent Events (SSE)
- Error handling with A2A error codes
- Type-safe request/response handling

## Usage

```go
package main

import (
    "log"
    "a2a/client"
    "a2a/models"
)

func main() {
    // Create a new client
    a2aClient := client.NewClient("http://localhost:8080")

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

    // Send a task
    response, err := a2aClient.SendTask(models.TaskSendParams{
        ID:      "task-1",
        Message: message,
    })
    if err != nil {
        log.Fatalf("Failed to send task: %v", err)
    }

    // Get the task from the response
    task, ok := response.Result.(*models.Task)
    if !ok {
        log.Fatalf("Expected result to be a Task")
    }

    // Use the task...
}
```

## API

### NewClient

```go
func NewClient(baseURL string) *Client
```

Creates a new A2A client instance with the specified base URL.

### Client Methods

#### SendTask

```go
func (c *Client) SendTask(params models.TaskSendParams) (*models.JSONRPCResponse, error)
```

Sends a new task to the agent. Returns a JSON-RPC response containing the task or an error.

#### GetTask

```go
func (c *Client) GetTask(params models.TaskQueryParams) (*models.JSONRPCResponse, error)
```

Gets the status of a task. Returns a JSON-RPC response containing the task or an error.

#### CancelTask

```go
func (c *Client) CancelTask(params models.TaskIDParams) (*models.JSONRPCResponse, error)
```

Cancels a task. Returns a JSON-RPC response containing the task or an error.

## Streaming Support

The client supports streaming task updates using Server-Sent Events (SSE). To use streaming:

1. Set the `Accept` header to `text/event-stream` in your request
2. The server will respond with a stream of task status updates
3. Each update will be a JSON object containing:
   - Task ID
   - Current status
   - Whether it's the final update

Example streaming usage:
```go
// Create a task with streaming
message := models.Message{
    Role: "user",
    Parts: []models.Part{
        {
            Type: stringPtr("text"),
            Text: stringPtr("Hello, A2A agent!"),
        },
    },
}

// Send a task with streaming enabled
response, err := a2aClient.SendTaskWithStreaming(models.TaskSendParams{
    ID:      "task-1",
    Message: message,
})
if err != nil {
    log.Fatalf("Failed to send task: %v", err)
}

// Process streaming updates
for update := range response.Updates {
    if update.Error != nil {
        log.Printf("Error: %v", update.Error)
        continue
    }
    
    // Process the update
    log.Printf("Task %s: %s", update.Result.ID, update.Result.Status.State)
}
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