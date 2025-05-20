# A2A Client (JS)

This directory contains a TypeScript client implementation for the Agent-to-Agent (A2A) communication protocol.

## `client.ts`

This file defines the `A2AClient` class, which provides methods for interacting with an A2A server over HTTP using JSON-RPC.

### Key Features:

- **JSON-RPC Communication:** Handles sending requests and receiving responses (both standard and streaming via Server-Sent Events) according to the JSON-RPC 2.0 specification.
- **A2A Methods:** Implements standard A2A methods like `sendTask`, `sendTaskSubscribe`, `getTask`, `cancelTask`, `setTaskPushNotification`, `getTaskPushNotification`, and `resubscribeTask`.
- **Error Handling:** Provides basic error handling for network issues and JSON-RPC errors.
- **Streaming Support:** Manages Server-Sent Events (SSE) for real-time task updates (`sendTaskSubscribe`, `resubscribeTask`).
- **Extensibility:** Allows providing a custom `fetch` implementation for different environments (e.g., Node.js).

### Basic Usage

```typescript
import { A2AClient, Task, TaskQueryParams, TaskSendParams } from "./client"; // Import necessary types
import { v4 as uuidv4 } from "uuid"; // Example for generating task IDs

const client = new A2AClient("http://localhost:41241"); // Replace with your server URL

async function run() {
  try {
    // Send a simple task (pass only params)
    const taskId = uuidv4();
    const sendParams: TaskSendParams = {
      id: taskId,
      message: { role: "user", parts: [{ text: "Hello, agent!", type: "text" }] },
    };
    // Method now returns Task | null directly
    const taskResult: Task | null = await client.sendTask(sendParams);
    console.log("Send Task Result:", taskResult);

    // Get task status (pass only params)
    const getParams: TaskQueryParams = { id: taskId };
    // Method now returns Task | null directly
    const getTaskResult: Task | null = await client.getTask(getParams);
    console.log("Get Task Result:", getTaskResult);
  } catch (error) {
    console.error("A2A Client Error:", error);
  }
}

run();
```

### Streaming Usage

```typescript
import {
  A2AClient,
  TaskStatusUpdateEvent,
  TaskArtifactUpdateEvent,
  TaskSendParams, // Use params type directly
} from "./client"; // Adjust path if necessary
import { v4 as uuidv4 } from "uuid";

const client = new A2AClient("http://localhost:41241");

async function streamTask() {
  const streamingTaskId = uuidv4();
  try {
    console.log(`\n--- Starting streaming task ${streamingTaskId} ---`);
    // Construct just the params
    const streamParams: TaskSendParams = {
      id: streamingTaskId,
      message: { role: "user", parts: [{ text: "Stream me some updates!", type: "text" }] },
    };
    // Pass only params to the client method
    const stream = client.sendTaskSubscribe(streamParams);

    // Stream now yields the event payloads directly
    for await (const event of stream) {
      // Type guard to differentiate events based on structure
      if ("status" in event) {
        // It's a TaskStatusUpdateEvent
        const statusEvent = event as TaskStatusUpdateEvent; // Cast for clarity
        console.log(
          `[${streamingTaskId}] Status Update: ${statusEvent.status.state} - ${
            statusEvent.status.message?.parts[0]?.text ?? "No message"
          }`
        );
        if (statusEvent.final) {
          console.log(`[${streamingTaskId}] Stream marked as final.`);
          break; // Exit loop when server signals completion
        }
      } else if ("artifact" in event) {
        // It's a TaskArtifactUpdateEvent
        const artifactEvent = event as TaskArtifactUpdateEvent; // Cast for clarity
        console.log(
          `[${streamingTaskId}] Artifact Update: ${
            artifactEvent.artifact.name ??
            `Index ${artifactEvent.artifact.index}`
          } - Part Count: ${artifactEvent.artifact.parts.length}`
        );
        // Process artifact content (e.g., artifactEvent.artifact.parts[0].text)
      } else {
        console.warn("Received unknown event structure:", event);
      }
    }
    console.log(`--- Streaming task ${streamingTaskId} finished ---`);
  } catch (error) {
    console.error(`Error during streaming task ${streamingTaskId}:`, error);
  }
}

streamTask();
```

This client is designed to work with servers implementing the A2A protocol specification.
