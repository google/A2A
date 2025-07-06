# Life of a Task

When a message is sent to an agent, it can choose to reply with either:

- A stateless `Message`.
- A stateful `Task` and zero or more `TaskStatusUpdateEvent` or `TaskArtifactUpdateEvent`.

If the response is a `Message`, the interaction is completed. On the other hand, A `Task` will keep getting updated until it is in an interrupted state (`input-required`, `auth-required`, or `user-consent-required`) or a terminal state (`completed`, `cancelled`, `rejected`, or `failed`). The `user-consent-required` state pauses the task until the end-user provides explicit consent for sensitive operations, such as booking travel or sharing personal data.

## Context

A contextId logically composes many Tasks and independent Messages. Agent implementor can manage the llm context based on these interactions, utilizing the `contextId`.

For the first time a message is sent, agent replies back with a contextId. If the agent responded with a task, then it will also have a taskId. Clients can send subsequent messages and attach the same contextID to indicate to the agent that they are continuing their previous interaction within the same context. Client also optionally attach the taskID to indicate that the message is in continuation of that specific task.

ContextId allows collaboration over a goal or share one session across multiple tasks.

## Agent: Message or a Task

Messages can be used for trivial interactions which do not require long-running processing or collaboration. An agent can use messages to negotiate the acceptance of a task. Once an agent maps the intent of an incoming message to a supported capability, it can reply back with a `Task`.

So conceptually there can be three levels of agents:

1. Always responds with Messages only. Doesn't do complex state management, no long running execution and uses contextID to tie messages together. Agent most probably directly wraps around an LLM invocation and simple tools.
2. Generates a task, does more substantial work that can be tracked and runs over extended life time.
3. Generates messages and tasks. Uses messages to negotiate agent capability and scope of work for a task. Then sends task to track its execution and collaborate over task states like more input-needed, error handling, etc.

An agent can choose to always reply back with task objects and model simple responses as tasks in `completed` state.

## Task Refinements & Follow-ups

Client may want to follow up with new asks based on the results of a task, refine upon the task results. This can be modeled by starting another interaction using the same contextID as the original task. Client can further hint the agent by providing the reference to the original task using `referenceTaskIds` in `Message` object. Agent would then either create a new `Task` or a `Message`.

Once a task has reached a terminal state (`completed`, `cancelled`, `rejected` or `failed`), it can't be restarted. There are some benefits to this:

- **Task Immutability**: Clients can reliably reference tasks and their associated state, artifacts, and messages. This provides a clean mapping of inputs to outputs. Useful for mapping client planner nodes to task execution.
- **Clear Unit of Work**: Every new request, refinement, or follow-up becomes a distinct task, simplifying bookkeeping and allowing for granular tracking of an agent's work.
    - Each artifact can be traced to a unit task.
    - This unit of work can be referenced much more granularly by parent agents or other systems like agent optimizers. Instead of restartable tasks, where all the subsequent refinements are clubbed together and would need to resort to some kind of message index range.
- **Easier Implementation**: Agent developers follow a simple rule: always create a new task for a request referring a task in terminal state.

### Parallel Follow-ups

Parallel work is supported by having the agent create distinct, parallel tasks for each follow-up message sent within the same contextId. This allows clients to track individual sub-tasks and create new dependent tasks as soon as a prerequisite task is complete.

For example:

```none
Task 1: Book a flight to Helsinki.
(After Task 1 finishes)
Task 2: Based on Task 1, book a hotel.
Task 3: Based on Task 1, book a snowmobile activity.
(After Task 2 finishes, while Task 3 is still in progress)
Task 4: Based on Task 2, add a spa reservation to the hotel booking.
```

### Referencing Previous Artifacts

The agent is responsible for inferring the relevant artifact from the referenced task or from the contextID. The serving agent is best suited to resolve ambiguity or identify missing information.

If there is ambiguity (e.g., multiple artifacts could fit the request), the agent will ask the client for clarification by returning an input-required state. The client can then specify the artifact in its response. Client can optionally populate artifact reference {artifactId, taskId} in part metadata. This allows for linkage between inputs for follow-up tasks and previous generated artifacts.

This approach allows for the client implementation to be simple.

### Tracking Artifact Mutation

A follow up or refinement can result in an older artifact being modified and newer artifacts being generated. It would be good to know this linkage and maybe track all mutations of the artifact to make sure only the latest copy is used for future context. Something like a linked list, with a head as the latest.

But the client is best suited, as well as is the real decider of what it considers as a result. And in fact can reject the mutation as well. Hence, the serving agent should not own this linkage and hence does not need to be part of A2A protocol spec. The serving agent should maintain the same artifact-name when generating a refinement on the original artifact.

For follow-up or refinement tasks, the client is best suited to refer to the "latest" or what it considers to be the intended artifact to be refined upon. If artifact reference is not explicitly specified, the serving agent can:

Use context to figure out the latest artifact.
Or in case of ambiguity or context not supported, agent can use "input-required".

### Example Follow-up

#### Client sends message to agent

```json
{
  "jsonrpc": "2.0",
  "id": "req-001",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "kind": "text",
          "text": "Generate an image of a sailboat on the ocean."
        }
      ],
      "messageId": "msg-user-001"
    }
  }
}
```

#### Agent responds with boat image

```json
{
  "jsonrpc": "2.0",
  "id": "req-001",
  "result": {
    "id": "task-boat-gen-123",
    "contextId": "ctx-conversation-abc",
    "status": {
      "state": "completed",
    },
    "artifacts": [
      {
        "artifactId": "artifact-boat-v1-xyz",
        "name": "sailboat_image.png",
        "description": "A generated image of a sailboat on the ocean.",
        "parts": [
          {
            "kind": "file",
            "file": {
              "name": "sailboat_image.png",
              "mimeType": "image/png",
              "bytes": "<base64_encoded_png_data_of_a_sailboat>"
            }
          }
        ]
      }
    ],
    "kind": "task"
  }
}
```

#### Client asks for coloring the boat red

Refers to previous taskID and uses same contextId.

```json
{
  "jsonrpc": "2.0",
  "id": "req-002",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "messageId": "msg-user-002",
      "contextId": "ctx-conversation-abc", // Same contextId
      "referenceTaskIds": ["task-boat-gen-123"] // Optional: Referencing the previous task
      "parts": [
        {
          "kind": "text",
          "text": "That's great! Can you make the sailboat red?"
          // Optional: In case the agent asked for actual relevant artifact.
          // Client could provide the artifact data in parts.
          // Also it could add metadata to the part to
          // reference the specific artifact.
          // "metadata": {
          //   "referenceArtifacts: [
          //      {
          //        "artifactId": "artifact-boat-v1-xyz",
          //        "taskId": "task-boat-gen-123"
          //      }
          //   ]
          // }
        }
      ],
    }
  }
}
```

#### Agent responds with new image artifact

- Creates new task in same contextId.
- Boat image artifact has same name. but a new artifactId.

```json
{
  "jsonrpc": "2.0",
  "id": "req-002",
  "result": {
    "id": "task-boat-color-456", // New task ID
    "contextId": "ctx-conversation-abc", // Same contextId
    "status": {
      "state": "completed",
    },
    "artifacts": [
      {
        "artifactId": "artifact-boat-v2-red-pqr", // New artifactId
        "name": "sailboat_image.png", // Same name as the original artifact
        "description": "A generated image of a red sailboat on the ocean.",
        "parts": [
          {
            "kind": "file",
            "file": {
              "name": "sailboat_image.png",
              "mimeType": "image/png",
              "bytes": "<base64_encoded_png_data_of_a_RED_sailboat>"
            }
          }
        ]
      }
    ],
    "kind": "task"
  }
}
```

#### Requiring User Consent for a Sensitive Operation

The client requests the agent to book a flight, which requires user consent due to the sensitive nature of the operation.

##### Client sends message to agent
```json
{
  "jsonrpc": "2.0",
  "id": "req-003",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "kind": "text",
          "text": "Book a flight to Helsinki for next week."
        }
      ],
      "messageId": "msg-user-003",
      "contextId": "ctx-travel-xyz"
    }
  }
}
```
##### Agent responds with a task requiring consent

```json
{
  "jsonrpc": "2.0",
  "id": "req-003",
  "result": {
    "id": "task-flight-booking-789",
    "contextId": "ctx-travel-xyz",
    "status": {
      "state": "user-consent-required",
      "message": "Please confirm consent to proceed with booking the flight."
    },
    "artifacts": [],
    "kind": "task"
  }
}
```

##### Client provides consent

```json
{
  "jsonrpc": "2.0",
  "id": "req-004",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "messageId": "msg-user-004",
      "contextId": "ctx-travel-xyz",
      "referenceTaskIds": ["task-flight-booking-789"],
      "parts": [
        {
          "kind": "text",
          "text": "I consent to booking the flight."
        }
      ]
    }
  }
}
```

##### Agent completes the task

```json
{
  "jsonrpc": "2.0",
  "id": "req-004",
  "result": {
    "id": "task-flight-booking-789",
    "contextId": "ctx-travel-xyz",
    "status": {
      "state": "completed"
    },
    "artifacts": [
      {
        "artifactId": "artifact-flight-confirmation-abc",
        "name": "flight_confirmation.pdf",
        "description": "Flight booking confirmation for Helsinki.",
        "parts": [
          {
            "kind": "file",
            "file": {
              "name": "flight_confirmation.pdf",
              "mimeType": "application/pdf",
              "bytes": "<base64_encoded_pdf_data>"
            }
          }
        ]
      }
    ],
    "kind": "task"
  }
}
```




