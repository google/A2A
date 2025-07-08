# API Method Mappings

!!! info "About This Document"
    This document provides the mappings of the 3 different transport types we intend to support in A2A and how these are defined. Though not officially a REST API, the REST-like transport is referred to as the A2A REST API for simplicity.

The base URLs for the transports are:

- **JSON-RPC:** `{root_url}/` (Method name is in the POST body)
- **gRPC:** `{root_url}/a2a.A2AService/`
- **REST:** `{root_url}/`

---

### `tasks/get`

Retrieves a specific task by its ID.

=== "REST"
    *   **Method:** `GET`
    *   **URL:** `/v1/tasks/{id}`
    *   **Query Parameters:**
        ```typescript
        // All parameters are optional
        historyLength?: number
        ```
    *   **Response:**
        ```json
        // Returns a Task object
        ```

=== "gRPC"
    *   **Method:** `GetTask`
    *   **Request:**
        ```proto
        message GetTaskRequest {
          // name = "tasks/{id}"
          string name = 1;
          int32 history_length = 2;
        }
        ```
    *   **Response:**
        ```proto
        // Returns a Task message
        Task
        ```

=== "JSON-RPC"
    *   **Method:** `tasks/get`
    *   **Parameters:**
        ```typescript
        {
          id: string,
          metadata?: { [key: string]: any },
          historyLength?: number
        }
        ```
    *   **Response:**
        ```json
        // Returns a Task object
        ```

---

### `task/cancel`

Cancels a running task.

=== "REST"
    *   **Method:** `POST`
    *   **URL:** `/v1/tasks/{id}:cancel`
    *   **Request Body:** (Empty)
    *   **Response:**
        ```json
        // Returns the updated Task object
        ```

=== "gRPC"
    *   **Method:** `CancelTask`
    *   **Request:**
        ```proto
        message CancelTaskRequest {
          // name = "tasks/{id}"
          string name = 1;
        }
        ```
    *   **Response:**
        ```proto
        // Returns a Task message
        Task
        ```

=== "JSON-RPC"
    *   **Method:** `task/cancel`
    *   **Parameters:**
        ```typescript
        {
          id: string,
          metadata?: { [key: string]: any }
        }
        ```
    *   **Response:**
        ```json
        // Returns a Task object
        ```

---

### `message/send`

Sends a message, which may result in a new task or an immediate response.

=== "REST"
    *   **Method:** `POST`
    *   **URL:** `/v1/message:send`
    *   **Request Body:**
        ```typescript
        {
          message: Message,
          configuration?: MessageSendConfiguration,
          metadata?: { [key: string]: any }
        }
        ```
    *   **Response:**
        ```typescript
        // Returns one of a message or a task
        {
          message?: Message,
          task?: Task
        }
        ```

=== "gRPC"
    *   **Method:** `SendMessage`
    *   **Request:**
        ```proto
        message SendMessageRequest {
          Message msg = 1;
          SendMessageConfiguration configuration = 2;
        }
        ```
    *   **Response:**
        ```proto
        message SendMessageResponse {
          oneof payload {
            Task task = 1;
            Message msg = 2;
          }
        }
        ```

=== "JSON-RPC"
    *   **Method:** `message/send`
    *   **Parameters:**
        ```typescript
        {
          message: Message,
          configuration?: MessageSendConfiguration,
          metadata?: { [key: string]: any }
        }
        ```
    *   **Response:**
        ```json
        // Returns a Message object
        ```

---

### `message/stream`

Sends a message and streams back events, such as status or artifact updates.

=== "REST"
    *   **Method:** `POST`
    *   **URL:** `/v1/message:stream`
    *   **Request Body:**
        ```typescript
        {
          message: Message,
          configuration?: MessageSendConfiguration,
          metadata?: { [key: string]: any }
        }
        ```
    *   **Response (Streaming):**
        ```typescript
        // A stream of one of the following objects
        {
          message?: Message,
          task?: Task,
          statusUpdate?: TaskStatusUpdateEvent,
          artifactUpdate?: TaskArtifactUpdateEvent
        }
        ```

=== "gRPC"
    *   **Method:** `SendStreamingMessage`
    *   **Request:**
        ```proto
        message SendMessageRequest {
          Message msg = 1;
          SendMessageConfiguration configuration = 2;
        }
        ```
    *   **Response (Streaming):**
        ```proto
        message StreamResponse {
          oneof payload {
            Task task = 1;
            Message msg = 2;
            TaskStatusUpdateEvent status_update = 3;
            TaskArtifactUpdateEvent artifact_update = 4;
          }
        }
        ```

=== "JSON-RPC"
    *   **Method:** `message/stream`
    *   **Parameters:**
        ```typescript
        {
          message: Message,
          configuration?: MessageSendConfiguration,
          metadata?: { [key: string]: any }
        }
        ```
    *   **Response (Streaming):**
        ```json
        // A stream of Message, Task, TaskStatusUpdateEvent, or TaskArtifactUpdateEvent objects
        ```

---

### `tasks/resubscribe`

Resubscribes to a task's event stream.

=== "REST"
    *   **Method:** `POST`
    *   **URL:** `/v1/tasks/{id}:resubscribe`
    *   **Request Body:** (Empty)
    *   **Response (Streaming):**
        ```typescript
        // A stream of one of the following objects
        {
          message?: Message,
          task?: Task,
          statusUpdate?: TaskStatusUpdateEvent,
          artifactUpdate?: TaskArtifactUpdateEvent
        }
        ```
=== "gRPC"
    *   **Method:** `TaskSubscription`
    *   **Request:**
        ```proto
        message TaskSubscriptionRequest {
          // name = "tasks/{id}"
          string name = 1;
        }
        ```
    *   **Response (Streaming):**
        ```proto
        message StreamResponse {
          oneof payload {
            Task task = 1;
            Message msg = 2;
            TaskStatusUpdateEvent status_update = 3;
            TaskArtifactUpdateEvent artifact_update = 4;
          }
        }
        ```
=== "JSON-RPC"
    *   **Method:** `tasks/resubscribe`
    *   **Parameters:**
        ```typescript
        {
          id: string,
          metadata?: { [key: string]: any }
        }
        ```
    *   **Response (Streaming):**
        ```json
        // A stream of Message, Task, TaskStatusUpdateEvent, or TaskArtifactUpdateEvent objects
        ```

---

### `tasks/pushNotificationConfig/get`

Retrieves a specific push notification configuration for a task.

=== "REST"
    *   **Method:** `GET`
    *   **URL:** `/v1/tasks/{taskId}/pushNotificationConfigs/{configId}`
    *   **Response:**
        ```json
        // Returns a TaskPushNotificationConfig object
        ```
=== "gRPC"
    *   **Method:** `GetTaskPushNotification`
    *   **Request:**
        ```proto
        message TaskSubscriptionRequest {
          // name = "tasks/{taskId}/pushNotification/{configId}"
          string name = 1;
        }
        ```
    *   **Response:**
        ```proto
        // Returns a TaskPushNotificationConfig message
        TaskPushNotificationConfig
        ```
=== "JSON-RPC"
    *   **Method:** `tasks/pushNotificationConfig/get`
    *   **Parameters:**
        ```typescript
        {
          id: string, // Corresponds to the full resource name
          metadata?: { [key: string]: any }
        }
        ```
    *   **Response:**
        ```json
        // Returns a TaskPushNotificationConfig object
        ```

---

### `tasks/pushNotificationConfig/set`

Creates or updates a push notification configuration for a task.

=== "REST"
    *   **Method:** `POST`
    *   **URL:** `/v1/tasks/{id}/pushNotificationConfigs`
    *   **Request Body:**
        ```typescript
        {
          config: TaskPushNotificationConfig
        }
        ```
    *   **Response:**
        ```json
        // Returns the created/updated TaskPushNotificationConfig object
        ```
=== "gRPC"
    *   **Method:** `CreateTaskPushNotification`
    *   **Request:**
        ```proto
        message SetTaskPushNotificationRequest {
          TaskPushNotificationConfig config = 1;
        }
        ```
    *   **Response:**
        ```proto
        // Returns the created/updated TaskPushNotificationConfig message
        TaskPushNotificationConfig
        ```
=== "JSON-RPC"
    *   **Method:** `tasks/pushNotificationConfig/set`
    *   **Parameters:**
        ```typescript
        // A TaskPushNotificationConfig object
        ```
    *   **Response:**
        ```json
        // Returns the created/updated TaskPushNotificationConfig object
        ```

---

### `card/get`

Retrieves the agent's card.

=== "REST"
    *   **Method:** `GET`
    *   **URL:** `/v1/card`
    *   **Request Body:** None
    *   **Response:**
        ```json
        // Returns an AgentCard object
        ```
=== "gRPC"
    *   **Method:** `GetAgentCard`
    *   **Request:** None (Empty)
    *   **Response:**
        ```proto
        // Returns an AgentCard message
        AgentCard
        ```
=== "JSON-RPC"
    *   This method is not currently defined for the JSON-RPC transport.

---

### `tasks/pushNotificationConfig/list`

Lists all push notification configurations for a given task.

=== "REST"
    *   **Method:** `GET`
    *   **URL:** `/v1/tasks/{id}/pushNotificationConfigs`
    *   **Response:**
        ```json
        // Returns an array of TaskPushNotificationConfig objects
        [ TaskPushNotificationConfig, ... ]
        ```
=== "gRPC"
    *   **Method:** `ListTaskPushNotification`
    *   **Request:**
        ```proto
        message ListTaskPushNotificationRequest {
          // parent = "tasks/{id}"
          string parent = 1;
        }
        ```
    *   **Response:**
        ```proto
        // Returns a repeated field of TaskPushNotificationConfig messages
        repeated TaskPushNotificationConfig
        ```
=== "JSON-RPC"
    *   Not applicable.

---

### `tasks/list`

Lists all tasks.

=== "REST"
    *   **Method:** `GET`
    *   **URL:** `/v1/tasks`
    *   **Request Body:** None
    *   **Response:**
        ```json
        // Returns an array of Task objects
        [ Task, ... ]
        ```
=== "gRPC"
    *   **Method:** `ListTask`
    *   **Request:** None (Empty)
    *   **Response:**
        ```proto
        // Returns a repeated field of Task messages
        repeated Task
        ```
=== "JSON-RPC"
    *   Not applicable.

### Caveats

* The REST API defines a wrapper structure for the streaming responses. This is not the same as the JSONRPC approach.
* The push notification setter method has a wrapper class for the input payload for REST as well. This is intended to make this more consistent with the gRPC approach
* The metadata fields at the request level are overly broad and hard to utilize. Removed these in the gRPC version.
* The REST API is based on the transcoding and best practices as defined by AIP-127.
