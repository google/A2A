/**
 * @title A2A
 */

/**
 * Represents the service provider of an agent.
 */
export interface AgentProvider {
  /** Agent provider's organization name*/
  organization: string;
  /** Agent provider's url */
  url: string;
}

/**
 * Defines optional capabilities supported by an agent.
 */
export interface AgentCapabilities {
  /** true if the agent supports SSE */
  streaming?: boolean;
  /** true if the agent can notify updates to client */
  pushNotifications?: boolean;
  /** true if the agent exposes status change history for tasks */
  stateTransitionHistory?: boolean;
}

/**
 * Defines authentication requirements for an agent.
 * Intended to match OpenAPI authentication structure.
 */
export interface AgentAuthentication {
  /** e.g. Basic, Bearer */
  schemes: string[];
  /** credentials a client should use for private cards */
  credentials?: string;
}

/**
 * Represents a unit of capability that an agent can perform.
 */
export interface AgentSkill {
  /** unique identifier for the agent's skill */
  id: string;
  /** human readable name of the skill */
  name: string;
  /**
   * description of the skill - will be used by the client or a human
   * as a hint to understand what the skill does.
   */
  description: string;
  /**
   * Set of tagwords describing classes of capabilities for this specific
   * skill.
   * @example ["cooking", "customer support", "billing"]
   */
  tags: string[];
  /**
   * The set of example scenarios that the skill can perform.
   * Will be used by the client as a hint to understand how the skill can be
   * used.
   * @example ["I need a recipe for bread"]
   */
  examples?: string[]; // example prompts for tasks
  /**
   * The set of interaction modes that the skill supports
   * (if different than the default).
   * Supported mime types for input.
   */
  inputModes?: string[];
  /** Supported mime types for output. */
  outputModes?: string[];
}

/**
 * An AgentCard conveys key information:
 * - Overall details (version, name, description, uses)
 * - Skills: A set of capabilities the agent can perform
 * - Default modalities/content types supported by the agent.
 * - Authentication requirements
 */
export interface AgentCard {
  /**
   * Human readable name of the agent.
   * @example "Recipe Agent"
   */
  name: string;
  /**
   * A human-readable description of the agent. Used to assist users and
   * other agents in understanding what the agent can do.
   * @example "Agent that helps users with recipes and cooking."
   */
  description: string;
  /** A URL to the address the agent is hosted at. */
  url: string;
  /** The service provider of the agent */
  provider?: AgentProvider;
  /**
   * The version of the agent - format is up to the provider.
   * @example "1.0.0"
   */
  version: string;
  /** A URL to documentation for the agent. */
  documentationUrl?: string;
  /** Optional capabilities supported by the agent. */
  capabilities: AgentCapabilities;
  /** Authentication requirements for the agent. */
  authentication: AgentAuthentication;
  /**
   * The set of interaction modes that the agent
   * supports across all skills. This can be overridden per-skill.
   * Supported mime types for input.
   */
  defaultInputModes: string[];
  /** Supported mime types for output. */
  defaultOutputModes: string[];
  /** Skills are a unit of capability that an agent can perform. */
  skills: AgentSkill[];
}

export interface Task {
  /** unique identifier for the task */
  id: string;
  /** server-generated id for contextual alignment across interactions */
  contextId: string;
  /** current status of the task */
  status: TaskStatus;
  history?: Message[];
  /** collection of artifacts created by the agent. */
  artifacts?: Artifact[];
  /** extension metadata */
  metadata?: object;
  /** event type */
  itemType: "task";
}

/** TaskState and accompanying message. */
export interface TaskStatus {
  state: TaskState;
  /** additional status updates for client */
  message?: Message;
  /**
  * ISO 8601 datetime string when the status was recorded.
  * @example "2023-10-27T10:00:00Z"
  * */
  timestamp?: string;
}

/** sent by server during sendStream or subscribe requests */
export interface TaskStatusUpdateEvent {
  /** Task id */
  taskId: string;
  /** the context the task is associated with */
  contextId: string;
  /** event type */
  itemType: "status-update";
  /** current status of the task */
  status: TaskStatus;
  /** indicates the end of the event stream */
  final: boolean;
  /** extension metadata */
  metadata?: object;
}

/** sent by server during sendStream or subscribe requests */
export interface TaskArtifactUpdateEvent {
  /** Task id */
  taskId: string;
  /** the context the task is associated with */
  contextId: string;
  /** event type */
  itemType: "artifact-update";
  /** generated artifact */
  artifact: Artifact;
  /** Indicates if this artifact appends to a previous one */
  append?: boolean;
  /** Indicates if this is the last chunk of the artifact */
  lastChunk?: boolean;
  /** extension metadata */
  metadata?: object;
}

/** Parameters containing only a task ID, used for simple task operations. */
export interface TaskIdParams {
  /** task id */
  id: string;
  metadata?: object;
}

/** Parameters for querying a task, including optional history length. */
export interface TaskQueryParams extends TaskIdParams {
  /** number of recent messages to be retrieved */
  historyLength?: number;
}

/**Configuration for the send message request */
export interface MessageSendConfiguration {
  /** accepted output modalities by the client */
  acceptedOutputModes: string[];
  /** number of recent messages to be retrieved */
  historyLength?: number;
  /** where the server should send notifications when disconnected. */
  pushNotificationConfig?: PushNotificationConfig;
  /** If the server should treat the client as a blocking request */
  blocking?: boolean;
}

/** Sent by the client to the agent as a request. May create, continue or restart a task. */
export interface MessageSendParams {
  /** The message being sent to the server */
  message: Message;
  /** Send message configuration */
  configuration?: MessageSendConfiguration;
  /** extension metadata */
  metadata?: object;
}

/** Represents the possible states of a Task. */
export enum TaskState {
  Submitted = "submitted",
  Working = "working",
  InputRequired = "input-required",
  Completed = "completed",
  Canceled = "canceled",
  Failed = "failed",
  Rejected = "rejected",
  AuthRequired = "auth-required",
  Unknown = "unknown",
}

/** Represents an artifact generated for a task task. */
export interface Artifact {
  /** unique identifier for the artifact */
  artifactId: string;
  /** Optional name for the artifact */
  name?: string;
  /** Optional description for the artifact */
  description?: string;
  /** artifact parts */
  parts: Part[];
  /** extension metadata */
  metadata?: object;
}

/** Represents a single message exchanged between user and agent. */
export interface Message {
  /** message sender's role */
  role: "user" | "agent";
  /** message content */
  parts: Part[];
  /** extension metadata */
  metadata?: object;
  /** identifier created by the message creator*/
  messageId: string;
  /** identifier of task the message is related to */
  taskId?: string;
  /** the context the message is associated with */
  contextId?: string;
  /** indicates the end of the event stream */
  final?: boolean;
  /** event type */
  itemType: "message";
}

/** Base properties common to all message parts. */
export interface PartBase {
  /** Optional metadata associated with the part. */
  metadata?: object;
}

/** Represents a text segment within parts.*/
export interface TextPart extends PartBase {
  /** Part type - text for TextParts*/
  itemType: "text";
  /** Text content */
  text: string;
}

/** Represents the base entity for FileParts */
export interface FileBase {
  /** Optional name for the file */
  name?: string;
  /** Optional mimeType for the file */
  mimeType?: string;
}

/** Define the variant where 'bytes' is present and 'uri' is absent */
export interface FileWithBytes extends FileBase {
  /** base64 encoded content of the file*/
  bytes: string;
  uri?: never;
}

/** Define the variant where 'uri' is present and 'bytes' is absent  */
export interface FileWithUri extends FileBase {
  uri: string;
  bytes?: never;
}

/** Represents a File segment within parts.*/
export interface FilePart extends PartBase {
  /** Part type - file for FileParts */
  itemType: "file";
  /** File content either as url or bytes */
  file: FileWithBytes | FileWithUri;
}

type RecordStringAny = {
  [key: string]: any;
};

/** Represents a structured data segment within a message part. */
export interface DataPart extends PartBase {
  /** Part type - data for DataParts */
  itemType: "data";
  /** Structured data content 
  */
  data: Record<string, any>;
}

/** Represents a part of a message, which can be text, a file, or structured data. */
export type Part = TextPart | FilePart | DataPart

/** Defines authentication details for push notifications. */
export interface PushNotificationAuthenticationInfo {
  /** Supported authentication schemes - e.g. Basic, Bearer */
  schemes: string[];
  /** Optional credentials */
  credentials?: string;
}

/**Configuration for setting up push notifications for task updates. */
export interface PushNotificationConfig {
  /** url for sending the push notifications */
  url: string;
  /** token unique to this task/session */
  token?: string;
  authentication?: PushNotificationAuthenticationInfo;
}

/**Parameters for setting or getting push notification configuration for a task */
export interface TaskPushNotificationConfig {
  /** task id */
  taskId: string;
  pushNotificationConfig: PushNotificationConfig;
}


/**
 * Base interface for any JSON-RPC 2.0 request or response.
 */
export interface JSONRPCMessage {
  /**
   * Specifies the version of the JSON-RPC protocol. MUST be exactly "2.0".
   */
  readonly jsonrpc: "2.0";

  /**
   * An identifier established by the Client that MUST contain a String, Number
   * Numbers SHOULD NOT contain fractional parts.   
   */
  id?: number | string;
}

/**
 * Represents a JSON-RPC 2.0 Request object.
 */
export interface JSONRPCRequest extends JSONRPCMessage {
  /**
   * A String containing the name of the method to be invoked.
   */
  method: string;

  /**
   * A Structured value that holds the parameter values to be used during the invocation of the method.
   */
  params?: { [key: string]: any };
}

/**
 * Represents a JSON-RPC 2.0 Error object.
 * This is typically included in a JSONRPCErrorResponse when an error occurs.
 */
export interface JSONRPCError {
  /**
   * A Number that indicates the error type that occurred.
   */
  code: number;

  /**
   * A String providing a short description of the error.
   */
  message: string;

  /**
   * A Primitive or Structured value that contains additional information about the error.
   * This may be omitted.
   */
  data?: any;
}

/**
 * Represents a JSON-RPC 2.0 Result object.
 */
interface JSONRPCResult extends JSONRPCMessage {
  /**
   * The result object on success
   */
  result: any;

  error?: never; // Optional 'never' helps enforce exclusivity
}


/**
 * Represents a JSON-RPC 2.0 Error Response object.
 */
export interface JSONRPCErrorResponse extends JSONRPCMessage {
  result?: never; // Optional 'never' helps enforce exclusivity
  error: JSONRPCError | A2AError
}

/**
 * Represents a JSON-RPC 2.0 Response object.
 */
export type JSONRPCResponse = SendMessageResponse | SendStreamingMessageResponse | GetTaskResponse | CancelTaskResponse | SetTaskPushNotificationConfigResponse | GetTaskPushNotificationConfigResponse;

/**
 * JSON-RPC request model for the 'message/send' method.
 */
export interface SendMessageRequest extends JSONRPCRequest {
  method: "message/send";
  params: MessageSendParams;
}

/**
 * JSON-RPC success response model for the 'message/send' method.
 */
export interface SendMessageSuccessResponse extends JSONRPCResult {
  result: Message | Task;
}

/**
 * JSON-RPC response model for the 'message/send' method.
 */
export type SendMessageResponse = SendMessageSuccessResponse | JSONRPCErrorResponse;

/**
 * JSON-RPC request model for the 'message/stream' method.
 */
export interface SendStreamingMessageRequest extends JSONRPCRequest {
  method: "message/stream";
  params: MessageSendParams;
}

/**
 * JSON-RPC success response model for the 'message/stream' method.
 */
export interface SendStreamingMessageSuccessResponse extends JSONRPCResult {
  result: Message | Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent;
}

/**
 * JSON-RPC response model for the 'message/stream' method.
 */
export type SendStreamingMessageResponse = SendStreamingMessageSuccessResponse | JSONRPCErrorResponse;


/**
 * JSON-RPC request model for the 'tasks/get' method.
 */
export interface GetTaskRequest extends JSONRPCRequest {
  method: "tasks/get";
  params: TaskQueryParams;
}

/**
 * JSON-RPC success response for the 'tasks/get' method.
 */
export interface GetTaskSuccessResponse extends JSONRPCResult {
  result: Task;
}

/**
 * JSON-RPC success response for the 'tasks/get' method.
 */
export type GetTaskResponse = GetTaskSuccessResponse | JSONRPCErrorResponse;

/**
 * JSON-RPC request model for the 'tasks/cancel' method.
 */
export interface CancelTaskRequest extends JSONRPCRequest {
  method: "tasks/cancel";
  params: TaskIdParams;
}

/**
 * JSON-RPC success response model for the 'tasks/cancel' method.
 */
export interface CancelTaskSuccessResponse extends JSONRPCResult {
  result: Task;
}

/**
 * JSON-RPC response for the 'tasks/cancel' method.
 */
export type CancelTaskResponse = CancelTaskSuccessResponse | JSONRPCErrorResponse;

/**
 * JSON-RPC request model for the 'tasks/pushNotificationConfig/set' method.
 */
export interface SetTaskPushNotificationConfigRequest extends JSONRPCRequest {
  method: "tasks/pushNotificationConfig/set";
  params: TaskPushNotificationConfig;
}

/**
 * JSON-RPC success response model for the 'tasks/pushNotificationConfig/set' method.
 */
export interface SetTaskPushNotificationConfigSuccessResponse extends JSONRPCResult {
  result: TaskPushNotificationConfig;
}

/**
 * JSON-RPC response for the 'tasks/pushNotificationConfig/set' method.
 */
export type SetTaskPushNotificationConfigResponse = SetTaskPushNotificationConfigSuccessResponse | JSONRPCErrorResponse;

/**
 * JSON-RPC request model for the 'tasks/pushNotificationConfig/get' method.
 */
export interface GetTaskPushNotificationConfigRequest extends JSONRPCRequest {
  method: "tasks/pushNotificationConfig/get";
  params: TaskIdParams;
}

/**
 * JSON-RPC success response model for the 'tasks/pushNotificationConfig/get' method.
 */
export interface GetTaskPushNotificationConfigSuccessResponse extends JSONRPCResult {
  result: TaskPushNotificationConfig;
}

/**
 * JSON-RPC response for the 'tasks/pushNotificationConfig/set' method.
 */
export type GetTaskPushNotificationConfigResponse = GetTaskPushNotificationConfigSuccessResponse | JSONRPCErrorResponse;


/**
 * JSON-RPC request model for the 'tasks/resubscribe' method.
 */
export interface TaskResubscriptionRequest extends JSONRPCRequest {
  method: "tasks/resubscribe";
  params: TaskIdParams;
}

/**
 * A2A supported request types
 */
export type A2ARequest =
  | SendMessageRequest
  | SendStreamingMessageRequest
  | GetTaskRequest
  | CancelTaskRequest
  | SetTaskPushNotificationConfigRequest
  | GetTaskPushNotificationConfigRequest
  | TaskResubscriptionRequest;

/**
 * JSON-RPC error indicating invalid JSON was received by the server.
 */
export interface JSONParseError extends JSONRPCError {
  code: -32700;
  /**
   * @default Invalid JSON payload
   */
  message: string;
}

/**
 * JSON-RPC error indicating the JSON sent is not a valid Request object.
 */
export interface InvalidRequestError extends JSONRPCError {
  code: -32600;
  /**
   * @default Request payload validation error
   */
  message: string;
}

/**
 * JSON-RPC error indicating the method does not exist or is not available.
 */
export interface MethodNotFoundError extends JSONRPCError {
  code: -32601;
  /**
   * @default Method not found
   */
  message: string;
}

/**
 * JSON-RPC error indicating invalid method parameter(s).
 */
export interface InvalidParamsError extends JSONRPCError {
  code: -32602;
  /**
   * @default Invalid parameters
   */
  message: string;
}

/**
 * JSON-RPC error indicating an internal JSON-RPC error on the server.
 */
export interface InternalError extends JSONRPCError {
  code: -32603;
  /**
   * @default Internal error
   */
  message: string;
}


/**
 * A2A specific error indicating the requested task ID was not found.
 */
export interface TaskNotFoundError extends JSONRPCError {
  code: -32001;
  /**
   * @default Task not found
   */
  message: string;
}

/**
 * A2A specific error indicating the task is in a state where it cannot be canceled.
 */
export interface TaskNotCancelableError extends JSONRPCError {
  code: -32002;
  /**
   * @default Task cannot be canceled
   */
  message: string
}

/**
 * A2A specific error indicating the agent does not support push notifications.
 */
export interface PushNotificationNotSupportedError extends JSONRPCError {
  code: -32003;
  /**
   * @default Push Notification is not supported
   */
  message: string
}

/**
 * A2A specific error indicating the requested operation is not supported by the agent.
 */
export interface UnsupportedOperationError extends JSONRPCError {
  code: -32004;
  /**
   * @default This operation is not supported
   */
  message: string
}

/**
 * A2A specific error indicating incompatible content types between request and agent capabilities.
 */
export interface ContentTypeNotSupportedError extends JSONRPCError {
  code: -32005;
  /**
   * @default Incompatible content types
   */
  message: string;
}

/**
 * A2A specific error indicating agent returned invalid response for the current method
 */
export interface InvalidAgentResponseError extends JSONRPCError {
  code: -32006;
  /**
   * @default Invalid agent response
   */
  message: string;
}

export type A2AError =
  | JSONParseError
  | InvalidRequestError
  | MethodNotFoundError
  | InvalidParamsError
  | InternalError
  | TaskNotFoundError
  | TaskNotCancelableError
  | PushNotificationNotSupportedError
  | UnsupportedOperationError
  | ContentTypeNotSupportedError
  | InvalidAgentResponseError;