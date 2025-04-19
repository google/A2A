# A2A Client (JS/TS)

This directory contains a TypeScript client implementation for the Agent-to-Agent (A2A) communication protocol.

## `client.ts`

This file defines the `A2AClient` class, which provides methods for interacting with an A2A server over HTTP using JSON-RPC.

### Key Features:

-   **JSON-RPC Communication:** Handles sending requests and receiving responses (both standard and streaming via Server-Sent Events).
-   **A2A Methods (Tasks):** Implements standard A2A methods like `sendTask`, `sendTaskSubscribe`, `getTask`, `cancelTask`, `setTaskPushNotification`, `getTaskPushNotification`, and `resubscribeTask`.
-   **A2A Methods (Knowledge Graph):** Implements new methods for KG collaboration: `knowledgeQuery`, `knowledgeUpdate`, `knowledgeSubscribe`. **Requires agent support.**
-   **GraphQL Support:** Primarily uses GraphQL for KG query/subscription methods.
-   **Error Handling:** Provides basic error handling for network issues and JSON-RPC errors (including new KG errors).
-   **Streaming Support:** Manages Server-Sent Events (SSE) for real-time task and knowledge graph updates.
-   **Capability Checks:** Includes a `supports()` method to check agent capabilities based on its card (fetched automatically).
-   **Extensibility:** Allows providing a custom `fetch` implementation.

### Basic Usage (Tasks)

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

### Streaming Usage (Tasks)

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
  if (!(await client.supports("streaming"))) {
     console.log("Agent does not support streaming tasks.");
     return;
  }
  const streamingTaskId = uuidv4();
  try {
    console.log(`\n--- Starting streaming task ${streamingTaskId} ---`);
    const streamParams: TaskSendParams = {
      id: streamingTaskId,
      message: { role: "user", parts: [{ text: "Stream me some updates!", type: "text" }] },
    };
    const stream = client.sendTaskSubscribe(streamParams);

    // Stream yields the event payloads directly
    for await (const event of stream) {
      if ("status" in event) { // TaskStatusUpdateEvent
        console.log(`[${streamingTaskId}] Status: ${event.status.state}`);
        if (event.final) break;
      } else if ("artifact" in event) { // TaskArtifactUpdateEvent
        console.log(`[${streamingTaskId}] Artifact: ${event.artifact.name ?? 'unnamed'}`);
      }
    }
    console.log(`--- Streaming task ${streamingTaskId} finished ---`);
  } catch (error) {
    console.error(`Error during streaming task ${streamingTaskId}:`, error);
  }
}

streamTask();
```

### Knowledge Graph Usage (Examples)

**Note:** These require the target agent to support the `knowledgeGraph` capability.

```typescript
import {
  A2AClient,
  KnowledgeQueryParams,
  KnowledgeUpdateParams,
  KnowledgeSubscribeParams,
  KnowledgeGraphPatch,
  PatchOperationType,
  KGSubject, KGPredicate, KGObject, KGStatement,
  KnowledgeGraphChangeEvent
} from "./client"; // Adjust path

const client = new A2AClient("http://localhost:41241"); // Agent URL

async function interactWithKG() {
  if (!(await client.supports("knowledgeGraph"))) {
    console.log("Agent does not support Knowledge Graph features.");
    return;
  }
  console.log("Agent supports Knowledge Graph features.");

  try {
    // 1. Query Knowledge
    const queryParams: KnowledgeQueryParams = {
      queryLanguage: "graphql",
      query: `query GetProjectStatus($projId: ID!) {
        project(id: $projId) {
          id
          status
          lastUpdatedBy { agentId }
        }
      }`,
      variables: { projId: "project-alpha" },
      requiredCertainty: 0.8,
    };
    const queryResult = await client.knowledgeQuery(queryParams);
    console.log("Knowledge Query Result:", JSON.stringify(queryResult?.data, null, 2));

    // 2. Update Knowledge
    const subject: KGSubject = { id: "project-alpha" };
    const predicate: KGPredicate = { id: "ex:reviewedBy" };
    const object: KGObject = { id: "agent-reviewer-01" }; // Resource object
    const statement: KGStatement = { subject, predicate, object, certainty: 0.99 };
    const patch: KnowledgeGraphPatch = { op: PatchOperationType.ADD, statement };

    const updateParams: KnowledgeUpdateParams = {
      mutations: [patch],
      sourceAgentId: "client-script-agent",
      justification: "Marking project as reviewed by reviewer 01.",
    };
    const updateResult = await client.knowledgeUpdate(updateParams);
    console.log("Knowledge Update Result:", updateResult);

    // 3. Subscribe to Knowledge (Requires Streaming capability too)
    if (await client.supports("streaming")) {
        const subscribeParams: KnowledgeSubscribeParams = {
            queryLanguage: "graphql",
            subscriptionQuery: `subscription OnProjectUpdate($projId: ID!) {
                projectUpdates(projectId: $projId) {
                    op
                    statement { subject { id } predicate { id } object { id value } }
                    changeId
                    timestamp
                }
            }`,
            variables: { projId: "project-alpha" },
        };

        console.log("\n--- Subscribing to KG updates for project-alpha ---");
        const subscription = client.knowledgeSubscribe(subscribeParams);
        // Listen for a few events or timeout
        const timeoutPromise = new Promise(resolve => setTimeout(resolve, 10000)); // 10 sec timeout
        const eventPromise = (async () => {
             for await (const changeEvent of subscription) {
                 console.log("Received KG Change Event:", changeEvent);
                 // Add logic to stop after N events if desired
             }
        })();

        await Promise.race([eventPromise, timeoutPromise]);
        console.log("--- Subscription finished or timed out ---");
        // Note: Actual cancellation/cleanup of server-side subscription might need another mechanism if required.

    } else {
        console.log("Agent does not support streaming for KG subscriptions.");
    }

  } catch (error) {
    console.error("Error during KG interaction:", error);
  }
}

interactWithKG();
```

This client provides the building blocks for creating sophisticated agent interactions based on the A2A protocol.