## Sample Methods and JSON Responses

### Sample Agent Card

=== "Agent Card"

    ```json
    {
      "name": "Google Maps Agent",
      "description": "Plan routes, remember places, and generate directions",
      "url": "https://maps-agent.google.com",
      "provider": {
        "organization": "Google",
        "url": "https://google.com"
      },
      "version": "1.0.0",
      "authentication": {
        "schemes": "OAuth2"
      },
      "defaultInputModes": [
        "text/plain"
      ],
      "defaultOutputModes": [
        "text/plain",
        "application/html"
      ],
      "capabilities": {
        "streaming": true,
        "pushNotifications": false
      },
      "skills": [
        {
          "id": "route-planner",
          "name": "Route planning",
          "description": "Helps plan routing between two locations",
          "tags": [
            "maps",
            "routing",
            "navigation"
          ],
          "examples": [
            "plan my route from Sunnyvale to Mountain View",
            "what's the commute time from Sunnyvale to San Francisco at 9AM",
            "create turn by turn directions from Sunnyvale to Mountain View"
          ],
          "outputModes": [
            "application/html",
            "video/mp4"
          ]
        },
        {
          "id": "custom-map",
          "name": "My Map",
          "description": "Manage a custom map with your own saved places",
          "tags": [
            "custom-map",
            "saved-places"
          ],
          "examples": [
            "show me my favorite restaurants on the map",
            "create a visual of all places I've visited in the past year"
          ],
          "outputModes": [
            "application/html"
          ]
        }
      ]
    }
    ```

### Send a Message

Allows a client to send content to a remote agent to interact, start a new Task, resume an interrupted Task, or reopen a completed Task. A Task interrupt may be caused by an agent requiring additional user input or a runtime error.

=== "Request"

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "text",
          "text": "tell me a joke"
        }
      ],
      "messageId": "9229e770-767c-417b-a0b0-f0741243c589"
    },
    "metadata": {}
  }
}
```

**Response - agent creates a Task:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "id": "363422be-b0f9-4692-a24d-278670e7c7f1",
    "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4",
    "status": {
      "state": "completed"
    },
    "artifacts": [
      {
        "name": "joke",
        "parts": [
          {
            "type": "text",
            "text": "Why did the chicken cross the road? To get to the other side!"
          }
        ]
      }
    ],
    "history": [
    {
      "role": "user",
      "parts": [
        {
          "type": "text",
          "text": "tell me a joke"
        }
      ],
      "messageId": "9229e770-767c-417b-a0b0-f0741243c589",
      "taskId": "363422be-b0f9-4692-a24d-278670e7c7f1",
      "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4"
    }
    ],
    "itemType": "task",
    "metadata": {}
  }
}
```

**Response - agent responds without a task:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "messageId": "363422be-b0f9-4692-a24d-278670e7c7f1",
    "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4",
    "parts": [
      {
        "type": "text",
        "text": "Why did the chicken cross the road? To get to the other side!"
      }
    ],
    "itemType": "message",
    "metadata": {}
  }
}
```

### Get a Task

Clients may use this method to retrieve the generated Artifacts for a Task. The agent determines the retention window for Tasks previously submitted to it. An agent may return an error code for Tasks that were past the retention window or for Tasks that are short-lived and not persisted.

The client may also request the last N items of history for the Task, which will include all Messages, in order, sent by the client and server. By default, this is 0 (no history).

=== "Request"

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tasks/get",
  "params": {
    "id": "363422be-b0f9-4692-a24d-278670e7c7f1",
    "historyLength": 10,
    "metadata": {}
  }
}
```

=== "Response"

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "id": "363422be-b0f9-4692-a24d-278670e7c7f1",
    "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4",
    "status": {
      "state": "completed"
    },
    "artifacts": [
      {
        "parts": [
          {
            "type": "text",
            "text": "Why did the chicken cross the road? To get to the other side!"
          }
        ]
      }
    ],
    "history": [
      {
        "role": "user",
        "parts": [
          {
            "type": "text",
            "text": "tell me a joke"
          }
        ],
        "messageId": "9229e770-767c-417b-a0b0-f0741243c589",
        "taskId": "363422be-b0f9-4692-a24d-278670e7c7f1",
        "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4"
      }
    ],
    "itemType": "task",
    "metadata": {}
  }
}
```

### Cancel a Task

A client may choose to cancel previously submitted Tasks.

=== "Request"

    ```json
    {
     "jsonrpc": "2.0",
     "id": 1,
     "method": "tasks/cancel",
     "params": {
      "id": "de38c76d-d54c-436c-8b9f-4c2703648d64",
      "metadata": {}
     }
    }
    ```

=== "Response"

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "id": "de38c76d-d54c-436c-8b9f-4c2703648d64",
    "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4",
    "status": {
      "state": "canceled"
    },
    "itemType": "task",
    "metadata": {}
  }
}
```

### Set Task Push Notifications

Clients may configure a push notification URL for receiving an update on Task status change.

=== "Request"

    ```json
    {
     "jsonrpc": "2.0",
     "id": 1,
     "method": "tasks/pushNotificationConfig/set",
     "params": {
      "taskId": "de38c76d-d54c-436c-8b9f-4c2703648d64",
      "pushNotificationConfig": {
       "url": "https://example.com/callback",
       "authentication": {
        "schemes": ["jwt"]
       }
      }
     }
    }
    ```

=== "Response"

    ```json
    {
     "jsonrpc": "2.0",
     "id": 1,
     "result": {
      "taskId": "de38c76d-d54c-436c-8b9f-4c2703648d64",
      "pushNotificationConfig": {
       "url": "https://example.com/callback",
       "authentication": {
        "schemes": ["jwt"]
       }
      }
     }
    }
    ```

### Get Task Push Notifications

Clients may retrieve the currently configured push notification configuration for a Task using this method.

=== "Request"

    ```json
    {
     "jsonrpc": "2.0",
     "id": 1,
     "method": "tasks/pushNotificationConfig/get",
     "params": {
      "id": "de38c76d-d54c-436c-8b9f-4c2703648d64"
     }
    }
    ```

=== "Response"

    ```json
    {
     "jsonrpc": "2.0",
     "id": 1,
     "result": {
      "taskId": "de38c76d-d54c-436c-8b9f-4c2703648d64",
      "pushNotificationConfig": {
       "url": "https://example.com/callback",
       "authentication": {
        "schemes": ["jwt"]
       }
      }
     }
    }
    ```

### Multi-turn Conversations

A Task may pause execution on the remote agent if it requires additional user input. When a Task is in the `input-required` state, the client must provide additional input for the Task to resume processing.

The Message included in the `input-required` state must include details indicating what the client must do (e.g., "fill out a form", "log into SaaS service foo"). If this includes structured data, the instruction should be sent as one `Part` and the structured data as a second `Part`.

**Interaction 1: Initial Request and Agent Prompt**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "text",
          "text": "request a new phone for me"
        }
      ],
      "messageId": "c53ba666-3f97-433c-a87b-6084276babe2"
    },
    "configuration": {
      "blocking": true,
    },
    "metadata": {}
  }
}
```

**Response (Sequence 2 - Input Required Status Update):**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "id": "3f36680c-7f37-4a5f-945e-d78981fafd36",
    "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4",
    "status": {
      "state": "input-required",
      "message": {
        "role": "agent",
        "parts": [
          {
            "type": "text",
            "text": "Select a phone type (iPhone/Android)"
          }
        ],
        "messageId": "c2e1b2dd-f200-4b04-bc22-1b0c65a1aad2",
        "taskId": "3f36680c-7f37-4a5f-945e-d78981fafd36",
        "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4"
      }
    },
    "history": [
      {
        "role": "user",
        "parts": [
          {
            "type": "text",
            "text": "request a new phone for me"
          }
        ],
        "messageId": "c53ba666-3f97-433c-a87b-6084276babe2",
        "taskId": "3f36680c-7f37-4a5f-945e-d78981fafd36",
        "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4"
      }
    ],
    "itemType": "task",
    "metadata": {}
  }
}
```
**Response (Sequence 3 - User Input):**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "text",
          "text": "Android"
        }
      ],
      "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4",
      "taskId": "3f36680c-7f37-4a5f-945e-d78981fafd36",
      "messageId": "0db1d6c4-3976-40ed-b9b8-0043ea7a03d3"
    },
    "configuration": {
      "blocking": true,
    },
    "metadata": {}
  }
}
```

**Response (Sequence 4 - Task Completion):**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "id": "3f36680c-7f37-4a5f-945e-d78981fafd36",
    "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4",
    "status": {
      "state": "completed"
    },
    "artifacts": [
      {
        "name": "order-confirmation",
        "parts": [
          {
            "type": "text",
            "text": "I have ordered a new Android device for you. Your request number is R12443"
          }
        ],
        "metadata": {}
      }
    ],
    "history": [
      {
        "role": "user",
        "parts": [
          {
            "type": "text",
            "text": "request a new phone for me"
          }
        ],
        "messageId": "c53ba666-3f97-433c-a87b-6084276babe2",
        "taskId": "3f36680c-7f37-4a5f-945e-d78981fafd36",
        "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4"
      },
      {
        "role": "agent",
        "parts": [
          {
            "type": "text",
            "text": "Select a phone type (iPhone/Android)"
          }
        ],
        "messageId": "c2e1b2dd-f200-4b04-bc22-1b0c65a1aad2",
        "taskId": "3f36680c-7f37-4a5f-945e-d78981fafd36",
        "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4"
      },
      {
        "role": "user",
        "parts": [
          {
            "type": "text",
            "text": "Android"
          }
        ],
        "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4",
        "taskId": "3f36680c-7f37-4a5f-945e-d78981fafd36",
        "messageId": "0db1d6c4-3976-40ed-b9b8-0043ea7a03d3"
      }
    ],
    "itemType": "task",
    "metadata": {}
  }
}
```


### Streaming Support

For clients and remote agents capable of communicating over HTTP with Server-Sent Events (SSE), clients can send the RPC request with method `message/stream` with the content. The remote agent can respond with either a single Message and end the stream, or a Task object with a stream of `TaskStatusUpdateEvents` (to communicate status changes or instructions/requests) and `TaskArtifactUpdateEvents` (to stream generated results).

Note that `TaskArtifactUpdateEvents` can append new parts to existing Artifacts. Clients can use `tasks/get` to retrieve the entire Artifact outside of the streaming context. Agents must set the `final: true` attribute at the end of the stream or if the agent is interrupted and requires additional user input.

=== "Request"

```json
{
  "method": "message/stream",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "text",
          "text": "write a long paper describing the attached pictures"
        },
        {
          "type": "file",
          "file": {
            "mimeType": "image/png",
            "data": "<base64-encoded-content>"
          }
        }
      ],
      "messageId": "bbb7dee1-cf5c-4683-8a6f-4114529da5eb"
    },
    "metadata": {}
  }
}
```

**Response (SSE Stream):**

```json
data: {
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "id": "225d6247-06ba-4cda-a08b-33ae35c8dcfa",
    "contextId": "05217e44-7e9f-473e-ab4f-2c2dde50a2b1",
    "status": {
      "state": "submitted",
      "timestamp":"2025-04-02T16:59:25.331844"
    },
    "history": [
      {
        "role": "user",
        "parts": [
          {
            "type": "text",
            "text": "write a long paper describing the attached pictures"
          },
          {
            "type": "file",
            "file": {
              "mimeType": "image/png",
              "data": "<base64-encoded-content>"
            }
          }
        ],
        "messageId": "bbb7dee1-cf5c-4683-8a6f-4114529da5eb",
        "taskId": "225d6247-06ba-4cda-a08b-33ae35c8dcfa",
        "contextId": "05217e44-7e9f-473e-ab4f-2c2dde50a2b1"
      }
    ],
    "itemType": "task",
    "metadata": {}
  }
}

data: {
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "taskId": "225d6247-06ba-4cda-a08b-33ae35c8dcfa",
    "contextId": "05217e44-7e9f-473e-ab4f-2c2dde50a2b1",
    "artifact": {
      "artifactId": "9b6934dd-37e3-4eb1-8766-962efaab63a1",
      "parts": [
        {"type":"text", "text": "<section 1...>"}
      ]
    },
    "append": false,
    "lastChunk": false,
    "itemType":"artifact-update"
  }
}

data: {
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "taskId": "225d6247-06ba-4cda-a08b-33ae35c8dcfa",
    "contextId": "05217e44-7e9f-473e-ab4f-2c2dde50a2b1",
    "artifact": {
      "artifactId": "9b6934dd-37e3-4eb1-8766-962efaab63a1",
      "parts": [
        {"type":"text", "text": "<section 2...>"}
      ],
    },
    "append": true,
    "lastChunk": false,
    "itemType":"artifact-update"
  }
}


data: {
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "taskId": "225d6247-06ba-4cda-a08b-33ae35c8dcfa",
    "contextId": "05217e44-7e9f-473e-ab4f-2c2dde50a2b1",
    "artifact": {
      "artifactId": "9b6934dd-37e3-4eb1-8766-962efaab63a1",
      "parts": [
        {"type":"text", "text": "<section 3...>"}
      ]
    },
    "append": true,
    "lastChunk": true,
    "itemType":"artifact-update"
  }
}

data: {
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "taskId": "225d6247-06ba-4cda-a08b-33ae35c8dcfa",
    "contextId": "05217e44-7e9f-473e-ab4f-2c2dde50a2b1",
    "status": {
      "state": "completed",
      "timestamp":"2025-04-02T16:59:35.331844"
    },
    "final": true,
    "itemType":"status-update"
  }
}
```

#### Resubscribe to Task

A disconnected client may resubscribe to a remote agent that supports streaming to receive Task updates via SSE.

=== "Request"

```json
{
  "method": "tasks/resubscribe",
  "params": {
    "id": "225d6247-06ba-4cda-a08b-33ae35c8dcfa",
    "metadata": {}
  }
}
```

**Response (SSE Stream):**

```json
data: {
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "taskId": "225d6247-06ba-4cda-a08b-33ae35c8dcfa",
    "contextId": "05217e44-7e9f-473e-ab4f-2c2dde50a2b1",
    "artifact": {
      "artifactId": "9b6934dd-37e3-4eb1-8766-962efaab63a1",
      "parts": [
        {"type":"text", "text": "<section 2...>"}
      ]
    },
    "append": true,
    "lastChunk":false,
    "itemType":"artifact-update"  
  }
}
    ```

data: {
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "taskId": "225d6247-06ba-4cda-a08b-33ae35c8dcfa",
    "contextId": "05217e44-7e9f-473e-ab4f-2c2dde50a2b1",
    "artifact": {
      "artifactId": "9b6934dd-37e3-4eb1-8766-962efaab63a1",
      "parts": [
        {"type":"text", "text": "<section 3...>"}
      ]
    },
    "append": true,
    "lastChunk": true,
    "itemType":"artifact-update"
  }
}


data: {
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "taskId": "225d6247-06ba-4cda-a08b-33ae35c8dcfa",
    "contextId": "05217e44-7e9f-473e-ab4f-2c2dde50a2b1",
    "status": {
      "state": "completed",
      "timestamp":"2025-04-02T16:59:35.331844"
    },
    "final": true,
    "itemType":"status-update"
  }
}
```

### Non-textual Media

The following example demonstrates an interaction between a client and an agent involving non-textual data (a PDF file). This example uses polling by the client to get updates.

**Interaction 1: Send File and Acknowledgment**

```json
{
  "jsonrpc": "2.0",
  "id": 9,
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "text",
          "text": "Analyze the attached report and generate high level overview"
        },
        {
          "type": "file",
          "file": {
            "mimeType": "application/pdf",
            "data": "<base64-encoded-content>"
          }
        }
      ],
      "messageId": "6dbc13b5-bd57-4c2b-b503-24e381b6c8d6"
    },
    "configuration": {
      "blocking": false
    },
    "metadata": {}
  }
}
```

```json
{
  "jsonrpc": "2.0",
  "id": 9,
  "result": {
    "id": "43667960-d455-4453-b0cf-1bae4955270d",
    "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4",
    "status": {
      "state": "working",
      "message": {
        "role": "agent",
        "parts": [
          {
            "type": "text",
            "text": "analysis in progress, please wait"
          }
        ],
        "messageId": "bf9e5948-9b57-4324-910a-d8cd90df0dba",
        "taskId": "43667960-d455-4453-b0cf-1bae4955270d",
        "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4",
        "metadata": {}
      }
    },
    "history": [
      {
        "role": "user",
        "parts": [
          {
            "type": "text",
            "text": "Analyze the attached report and generate high level overview"
          },
          {
            "type": "file",
            "file": {
              "mimeType": "application/pdf",
              "data": "<base64-encoded-content>"
            }
          }
        ],
        "messageId": "6dbc13b5-bd57-4c2b-b503-24e381b6c8d6",
        "taskId": "43667960-d455-4453-b0cf-1bae4955270d",
        "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4"
      }
    ],
    "itemType": "task",
    "metadata": {}
  }
}
```
**Interaction 2: Get Task to check the status**

**
```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "method": "tasks/get",
  "params": {
    "id": "43667960-d455-4453-b0cf-1bae4955270d",
    "metadata": {}
  }
}
```

```json
{
  "jsonrpc": "2.0",
  "id": 9,
  "result": {
    "id": "43667960-d455-4453-b0cf-1bae4955270d",
    "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4",
    "status": {
      "state": "completed"
    },
    "artifacts": [      
      {
        "artifactId":"9b6934dd-37e3-4eb1-8766-962efaab63a1",
        "parts": [
          {
            "type": "text",
            "text": "<generated analysis content>"
          }
        ],
        "metadata": {}
      }
    ],
    "history": [
      {
        "role": "user",
        "parts": [
          {
            "type": "text",
            "text": "Analyze the attached report and generate high level overview"
          },
          {
            "type": "file",
            "file": {
              "mimeType": "application/pdf",
              "data": "<base64-encoded-content>"
            }
          }
        ],
        "messageId": "6dbc13b5-bd57-4c2b-b503-24e381b6c8d6",
        "taskId": "43667960-d455-4453-b0cf-1bae4955270d",
        "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4"
      },
      {
        "role": "agent",
        "parts": [
          {
            "type": "text",
            "text": "analysis in progress, please wait"
          }
        ],
        "messageId": "bf9e5948-9b57-4324-910a-d8cd90df0dba",
        "taskId": "43667960-d455-4453-b0cf-1bae4955270d",
        "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4"
      }
    ],
    "itemType": "task",
    "metadata": {}
  }
}
```

### Structured Output

Both the client and the agent can request structured output from the other party by specifying a `mimeType` and `schema` in the `metadata` of a `Part`.

=== "Request (Requesting JSON Output)"

```json
{
  "jsonrpc": "2.0",
  "id": 9,
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "text",
          "text": "Show me a list of my open IT tickets",
          "metadata": {
            "mimeType": "application/json",
            "schema": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "ticketNumber": { "type": "string" },
                  "description": { "type": "string" }
                }
              }
            }
          }
        }
      ],
      "messageId": "85b26db5-ffbb-4278-a5da-a7b09dea1b47"
    },
    "metadata": {}
  }
}
```

=== "Response (Providing JSON Output)"

```json
{
  "jsonrpc": "2.0",
  "id": 9,
  "result": {
    "id": "d8c6243f-5f7a-4f6f-821d-957ce51e856c",
    "contextId": "c295ea44-7543-4f78-b524-7a38915ad6e4",
    "status": {
      "state": "completed",
      "timestamp": "2025-04-17T17:47:09.680794"
    },
    "artifacts": [
      {
        "artifactId":"c5e0382f-b57f-4da7-87d8-b85171fad17c",
        "parts": [
          {
            "type": "text",
            "text": "[{\"ticketNumber\":\"REQ12312\",\"description\":\"request for VPN access\"},{\"ticketNumber\":\"REQ23422\",\"description\":\"Add to DL - team-gcp-onboarding\"}]"
          }
        ],
        "index": 0
      }
    ],
    "itemType": "task"
  }
}
```

### Error Handling

Following is the `ErrorMessage` format for the server to respond to the client when it encounters an error processing the client request.

```typescript
interface ErrorMessage {
  code: number;
  message: string;
  data?: any;
}
```

The following are the standard JSON-RPC error codes that the server can respond with for error scenarios:

| Error Code           | Message                          | Description                                            |
|:---------------------|:---------------------------------|:-------------------------------------------------------|
| `-32700`             | JSON parse error                 | Invalid JSON was sent                                  |
| `-32600`             | Invalid Request                  | Request payload validation error                       |
| `-32601`             | Method not found                 | Not a valid method                                     |
| `-32602`             | Invalid params                   | Invalid method parameters                              |
| `-32603`             | Internal error                   | Internal JSON-RPC error                                |
| `-32000` to `-32099` | Server error                     | Reserved for implementation specific error codes       |
| `-32001`             | Task not found                   | Task not found with the provided id                    |
| `-32002`             | Task cannot be canceled          | Task cannot be canceled by the remote agent            |
| `-32003`             | Push notifications not supported | Push Notification is not supported by the agent        |
| `-32004`             | Unsupported operation            | Operation is not supported                             |
| `-32005`             | Incompatible content types       | Incompatible content types between client and an agent |
| `-32006`             | Invalid agent response       | Agent returned invalid response for the current method |