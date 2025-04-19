# A2A Server (JS/TS)

This directory contains a TypeScript server implementation for the Agent-to-Agent (A2A) communication protocol, built using Express.js.

## Overview

The `A2AServer` class provides a framework for hosting an A2A-compliant agent. It handles:

-   Incoming JSON-RPC requests over HTTP.
-   Routing requests to the appropriate A2A methods (`tasks/send`, `tasks/get`, `knowledge/query`, etc.).
-   Managing task state persistence via a configurable `TaskStore`.
-   Handling streaming responses using Server-Sent Events (SSE) for methods like `tasks/sendSubscribe` and `knowledge/subscribe`.
-   Basic validation and error handling according to the JSON-RPC and A2A specifications.
-   Serving the agent's `AgentCard` via a `.well-known` endpoint.

## Basic Usage

```typescript
import {
  A2AServer,
  InMemoryTaskStore, // Or FileStore
  TaskContext,
  TaskYieldUpdate,
  schema // Import schema types if needed in handler
} from "./index"; // Assuming imports from the server package

// 1. Define your agent's core logic as a TaskHandler
// This generator handles the business logic for incoming tasks.
async function* myAgentLogic(
  context: TaskContext
): AsyncGenerator<TaskYieldUpdate, schema.Task | void, unknown> {
  console.log(`Handling task: ${context.task.id}`);
  const userInput = context.userMessage.parts.find(p => p.type === 'text')?.text ?? '';
  console.log(`User input: ${userInput}`);

  // Yield status updates
  yield {
    state: "working",
    message: { role: "agent", parts: [{ text: "Processing your request..." }] },
  };

  // Simulate work...
  await new Promise((resolve) => setTimeout(resolve, 1500));

  // Check for cancellation periodically
  if (context.isCancelled()) {
    console.log("Task cancelled!");
    yield { state: "canceled" }; // Yield final canceled state
    return; // Exit the handler
  }

  // Yield an artifact (e.g., a result file)
  yield {
    name: "result.txt",
    // mimeType: "text/plain", // Optional: Add mimeType if known
    parts: [{ type: "text", text: `Processed result for task ${context.task.id} based on input: ${userInput}` }],
  };

  // Yield final status
  yield {
    state: "completed",
    message: { role: "agent", parts: [{ text: "Task completed successfully!" }] },
  };

  // Non-streaming handlers might return the final Task object directly,
  // but yielding the final state is generally preferred for consistency.
  // return updatedTaskObject; // Optional return for tasks/send
}

// 2. Configure the server (Agent Card, Store)
const myAgentCard: schema.AgentCard = {
  name: "My Express Agent",
  version: "1.0.0",
  url: "http://localhost:41241/", // Adjust URL/port as needed
  capabilities: {
    streaming: true, // This agent supports streaming
    pushNotifications: false, // Does not support push notifications
    stateTransitionHistory: false,
    knowledgeGraph: false, // Does NOT support KG features (in this example)
    knowledgeGraphQueryLanguages: [],
  },
  skills: [{id: "default_handler", name: "Default Task Processor"}],
  // Add other card details (description, provider, auth, etc.)
};

const store = new InMemoryTaskStore(); // Use in-memory storage
// const store = new FileStore({ dir: './my-agent-tasks' }); // Use file storage

// 3. Create and start the server
const server = new A2AServer(myAgentLogic, { taskStore: store, card: myAgentCard });

server.start(41241); // Start listening on port 41241

console.log("A2A Server started on port 41241.");

```

## Task Handling

-   The core logic for your agent is implemented in the `TaskHandler` function passed to the `A2AServer` constructor.
-   This handler is an `async function*` (async generator).
-   It receives a `TaskContext` object containing the current `task` state, the triggering `userMessage`, task `history`, and a function `isCancelled()` to check for cancellation requests.
-   The handler performs its work and uses `yield` to send back updates:
    -   `yield { state: "...", message: ... }`: Updates the task status. The server adds the timestamp.
    -   `yield { name: "...", parts: [...] }`: Yields a new or updated `Artifact`.
-   For streaming methods (`tasks/sendSubscribe`), yielded updates are sent immediately to the client via SSE.
-   For non-streaming (`tasks/send`), yielded updates modify the task state internally, and the final task state is sent back in the response.
-   The server manages saving the task state to the `TaskStore` after processing each yield.

## Knowledge Graph Features

-   The A2A protocol **specifies** methods (`knowledge/query`, `knowledge/update`, `knowledge/subscribe`) for Knowledge Graph collaboration.
-   This server implementation includes the **routing** and basic **capability checks** for these methods based on the `AgentCard`.
-   However, the default `InMemoryTaskStore` and `FileStore` **do not implement** the actual KG backend logic (storage, GraphQL execution, subscription management). They provide placeholder methods that throw `UnsupportedOperationError`.
-   To fully support KG features, you would need to:
    1.  Set `knowledgeGraph: true` and `knowledgeGraphQueryLanguages: ["graphql"]` in your `AgentCard`.
    2.  Create a custom `TaskStore` (or a separate `KnowledgeStore`) that integrates with a KG database (e.g., RDFLib, GraphDB, Neo4j, Neptune) and a GraphQL engine (e.g., Ariadne, Apollo Server).
    3.  Implement the `knowledgeQuery`, `knowledgeUpdate`, and `knowledgeSubscribe` methods in your custom store to interact with your KG backend and GraphQL engine.

## Storage

-   **`InMemoryTaskStore`**: Stores task state and history in memory. Simple but data is lost on server restart. Good for development and testing.
-   **`FileStore`**: Persists task state and history as JSON files in a specified directory. Suitable for simple persistence needs.

You can implement the `TaskStore` interface to connect to other databases or storage systems.

## Error Handling

The server catches common errors (invalid requests, handler errors, store errors) and formats them into standard JSON-RPC error responses. Custom errors can be thrown using the `A2AError` class.

This server implementation provides a robust foundation for building A2A-compliant agents in TypeScript/JavaScript.