## Agent-to-Agent Communication

The communication between a Client and a Remote Agent is oriented towards **_task completion_** where agents collaboratively fulfill an end user's request. A Task object allows a Client and a Remote Agent to collaborate for completing the submitted task.

A task can be completed by a remote agent immediately or it can be long-running. For long-running tasks, the client may poll the agent for fetching the latest status. Agents can also push notifications to the client via SSE (if connected) or through an external notification service.

## Core Objects

### Task

A Task is a stateful entity that allows Clients and Remote Agents to achieve a specific outcome and generate results. Clients and Remote Agents exchange Messages within a Task. Remote Agents generate results as Artifacts.

A Task is always created by a Client and the status is always determined by the Remote Agent. Multiple Tasks may be part of a common session (denoted by optional sessionId) if required by the client. To do so, the Client sets an optional sessionId when creating the Task.

The agent may:

- fulfill the request immediately
- schedule work for later
- reject the request
- negotiate a different modality
- ask the client for more information
- delegate to other agents and systems

Even after fulfilling the goal, the client can request more information or a change in the context of that same Task. (For example client: "draw a picture of a rabbit", agent: "&lt;picture&gt;", client: "make it red").

Tasks are used to transmit [Artifacts](#artifact) (results) and [Messages](#message) (thoughts, instructions, anything else). Tasks maintain a status and an optional history of status and Messages.

```typescript
interface Task {
  id: string; // unique identifier for the task
  sessionId: string; // client-generated id for the session holding the task.
  status: TaskStatus; // current status of the task
  history?: Message[];
  artifacts?: Artifact[]; // collection of artifacts created by the agent.
  metadata?: Record<string, any>; // extension metadata
}
// TaskState and accompanying message.
interface TaskStatus {
  state: TaskState;
  message?: Message; //additional status updates for client
  timestamp?: string; // ISO datetime value
}
// sent by server during sendSubscribe or subscribe requests
interface TaskStatusUpdateEvent {
  id: string; //Task id
  status: TaskStatus;
  final: boolean; //indicates the end of the event stream
  metadata?: Record<string, any>;
}
// sent by server during sendSubscribe or subscribe requests
interface TaskArtifactUpdateEvent {
  id: string; //Task id
  artifact: Artifact;
  metadata?: Record<string, any>;
}
// Sent by the client to the agent to create, continue, or restart a task.
interface TaskSendParams {
  id: string;
  sessionId?: string; //server creates a new sessionId for new tasks if not set
  message: Message;
  historyLength?: number; //number of recent messages to be retrieved
  // where the server should send notifications when disconnected.
  pushNotification?: PushNotificationConfig;
  metadata?: Record<string, any>; // extension metadata
}
type TaskState =
  | "submitted"
  | "working"
  | "input-required"
  | "completed"
  | "canceled"
  | "failed"
  | "unknown";
```

### Artifact

Agents generate Artifacts as an end result of a Task. Artifacts are immutable, can be named, and can have multiple parts. A streaming response can append parts to existing Artifacts.

A single Task can generate many Artifacts. For example, "create a webpage" could create separate HTML and image Artifacts.

```typescript
interface Artifact {
  name?: string;
  description?: string;
  parts: Part[];
  metadata?: Record<string, any>;
  index: number;
  append?: boolean;
  lastChunk?: boolean;
}
```

### Message

A Message contains any content that is not an Artifact. This can include things like agent thoughts, user context, instructions, errors, status, or metadata.

All content from a client comes in the form of a Message. Agents send Messages to communicate status or to provide instructions (whereas generated results are sent as Artifacts).

A Message can have multiple parts to denote different pieces of content. For example, a user request could include a textual description from a user and then multiple files used as context from the client.

```typescript
interface Message {
  role: "user" | "agent";
  parts: Part[];
  metadata?: Record<string, any>;
}
```

### Part

A fully formed piece of content exchanged between a client and a remote agent as part of a Message or an Artifact. Each Part has its own content type and metadata.

```typescript
interface TextPart {
  type: "text";
  text: string;
}
interface FilePart {
  type: "file";
  file: {
    name?: string;
    mimeType?: string;
    // oneof {
    bytes?: string; //base64 encoded content
    uri?: string;
    //}
  };
}
interface DataPart {
  type: "data";
  data: Record<string, any>;
}
type Part = (TextPart | FilePart | DataPart) & {
  metadata: Record<string, any>;
};
```

### Push Notifications

A2A supports a secure notification mechanism whereby an agent can notify a client of an update outside of a connected session via a PushNotificationService. Within and across enterprises, it is critical that the agent verifies the identity of the notification service, authenticates itself with the service, and presents an identifier that ties the notification to the executing Task.

The target server of the PushNotificationService should be considered a separate service, and is not guaranteed (or even expected) to be the client directly. This PushNotificationService is responsible for authenticating and authorizing the agent and for proxying the verified notification to the appropriate endpoint (which could be anything from a pub/sub queue, to an email inbox or other service, etc).

For contrived scenarios with isolated client-agent pairs (e.g. local service mesh in a contained VPC, etc.) or isolated environments without enterprise security concerns, the client may choose to simply open a port and act as its own PushNotificationService. Any enterprise implementation will likely have a centralized service that authenticates the remote agents with trusted notification credentials and can handle online/offline scenarios. (This should be thought of similarly to a mobile Push Notification Service).

```typescript
interface PushNotificationConfig {
  url: string;
  token?: string; // token unique to this task/session
  authentication?: {
    schemes: string[];
    credentials?: string;
  };
}
interface TaskPushNotificationConfig {
  id: string; //task id
  pushNotificationConfig: PushNotificationConfig;
}
```
