// === JSON-RPC Base Structures ===

/** Base interface for identifying JSON-RPC messages. */
export interface JSONRPCMessageIdentifier {
  /** Request identifier. */
  id?: number | string | null;
}

/** Base interface for all JSON-RPC messages. */
export interface JSONRPCMessage extends JSONRPCMessageIdentifier {
  /** Must be "2.0". */
  jsonrpc?: "2.0";
}

/** Represents a JSON-RPC request object base structure. */
export interface JSONRPCRequest extends JSONRPCMessage {
  method: string;
  params?: unknown; // Specific requests will override
}

/** Represents a JSON-RPC error object. */
export interface JSONRPCError<Data = unknown | null, Code = number> {
  code: Code;
  message: string;
  data?: Data;
}

/** Represents a JSON-RPC response object. */
export interface JSONRPCResponse<R = unknown | null, E = unknown | null>
  extends JSONRPCMessage {
  result?: R;
  error?: JSONRPCError<E> | null;
}

// === Core A2A Data Structures ===

/** Represents the state of a task. */
export type TaskState =
  | "submitted"
  | "working"
  | "input-required"
  | "completed"
  | "canceled"
  | "failed"
  | "unknown";

/** Defines the authentication schemes and credentials for an agent. */
export interface AgentAuthentication {
  schemes: string[];
  credentials?: string | null;
}

/** Describes the capabilities of an agent. */
export interface AgentCapabilities {
  /** Supports streaming responses (tasks/sendSubscribe, knowledge/subscribe). Defaults to false. */
  streaming?: boolean;
  /** Supports server-sent push notifications for task updates. Defaults to false. */
  pushNotifications?: boolean;
  /** Tracks and provides task state transition history. Defaults to false. */
  stateTransitionHistory?: boolean;
  /** Supports knowledge graph methods (knowledge/*). Defaults to false. */
  knowledgeGraph?: boolean;
  /** List of query languages supported for KG interactions (e.g., 'graphql'). Defaults to []. */
  knowledgeGraphQueryLanguages?: ("graphql" | "sparql")[]; // Added sparql as potential future option
}

/** Represents the provider or organization behind an agent. */
export interface AgentProvider {
  organization: string;
  url?: string | null;
}

/** Defines a specific skill or capability offered by an agent. */
export interface AgentSkill {
  id: string;
  name: string;
  description?: string | null;
  tags?: string[] | null;
  examples?: string[] | null;
  inputModes?: string[] | null;
  outputModes?: string[] | null;
}

/** Represents the metadata card for an agent. */
export interface AgentCard {
  name: string;
  description?: string | null;
  url: string;
  provider?: AgentProvider | null;
  version: string;
  documentationUrl?: string | null;
  capabilities: AgentCapabilities;
  authentication?: AgentAuthentication | null;
  defaultInputModes?: string[];
  defaultOutputModes?: string[];
  skills: AgentSkill[];
}

/** Base for FileContent, DO NOT USE DIRECTLY. */
interface FileContentBase {
  name?: string | null;
  mimeType?: string | null;
  bytes?: string | null; // Base64 encoded
  uri?: string | null; // URI format
}
/** File content represented by inline Base64 bytes. */
export type FileContentBytes = FileContentBase & { bytes: string; uri?: never };
/** File content represented by a URI. */
export type FileContentUri = FileContentBase & { uri: string; bytes?: never };
/** Represents file content via bytes OR uri. */
export type FileContent = FileContentBytes | FileContentUri;

/** Represents a part of a message containing text content. */
export interface TextPart {
  type: "text";

  /**
   * The text content.
   */
  text: string;
  metadata?: Record<string, unknown> | null;
}

/** Represents a part of a message containing file content. */
export interface FilePart {
  /**
   * Type identifier for this part.
   */
  type: "file";

  /**
   * The file content, provided either inline or via URI.
   */
  file: FileContent;
  metadata?: Record<string, unknown> | null;
}

/** Represents a part of a message containing structured data (JSON). */
export interface DataPart {
  /**
   * Type identifier for this part.
   */
  type: "data";

  /**
   * The structured data content as a JSON object.
   */
  data: Record<string, unknown>;
  metadata?: Record<string, unknown> | null;
}

/** Union type for different message parts. */
export type Part = TextPart | FilePart | DataPart;

/** Represents an artifact generated or used by a task. */
export interface Artifact {
  name?: string | null;
  description?: string | null;
  parts: Part[];
  index?: number; // Default 0
  append?: boolean | null;
  lastChunk?: boolean | null;
  metadata?: Record<string, unknown> | null;
}

/** Represents a message exchanged between a user and an agent. */
export interface Message {
  role: "user" | "agent";
  parts: Part[];
  metadata?: Record<string, unknown> | null;
}

/** Represents the status of a task at a specific point in time. */
export interface TaskStatus {
  state: TaskState;
  message?: Message | null;
  /** ISO 8601 format timestamp. */
  timestamp: string; // Note: Server generates this, client provides Date
}

/** Represents a task being processed by an agent. */
export interface Task {
  id: string;
  sessionId?: string | null;
  status: TaskStatus;
  artifacts?: Artifact[] | null;
  /** Sequence of messages exchanged. May be truncated by server. */
  history?: Message[] | null;
  metadata?: Record<string, unknown> | null;
}

// === Streaming Event Types ===

/** Represents a status update event for a task (streaming). */
export interface TaskStatusUpdateEvent {
  id: string; // Task ID
  status: TaskStatus;
  /** Indicates if this is the terminal status update. */
  final?: boolean; // Default false
  metadata?: Record<string, unknown> | null;
}

/** Represents an artifact update event for a task (streaming). */
export interface TaskArtifactUpdateEvent {
  id: string; // Task ID
  artifact: Artifact;
  // Note: 'final' removed as it's less common for artifacts and wasn't in python test fix
  metadata?: Record<string, unknown> | null;
}

// === Authentication and Configuration ===

/** Extended AuthenticationInfo allowing extra properties. */
export interface AuthenticationInfo extends AgentAuthentication {
  [key: string]: any; // Allow additional properties
}

/** Configuration for push notifications. */
export interface PushNotificationConfig {
  /** URL endpoint for receiving notifications. */
  url: string; // format: uri
  /** Optional opaque token for simple authorization. */
  token?: string;
  authentication?: AuthenticationInfo | null;
}

// === Parameter Types for Requests ===

/** Parameters identifying a task. */
export interface TaskIdParams {
  id: string;
  metadata?: Record<string, unknown> | null;
}

/** Parameters for querying task details. */
export interface TaskQueryParams extends TaskIdParams {
  /** Max history length in response (null/0 omits). */
  historyLength?: number | null; // >= 0
}

/** Parameters for sending/initiating a task. */
export interface TaskSendParams {
  id: string;
  /** Defaults to a new UUID if omitted by client. */
  sessionId?: string;
  message: Message;
  /** MIME types the client accepts. */
  acceptedOutputModes?: string[] | null;
  pushNotification?: PushNotificationConfig | null;
  /** Max history length in response (null/0 omits). */
  historyLength?: number | null; // >= 0
  metadata?: Record<string, unknown> | null;
}

/** Parameters for setting push notification config. */
export interface TaskPushNotificationConfig {
  id: string;
  pushNotificationConfig: PushNotificationConfig;
}

// === Knowledge Graph Types ===

/** Represents the subject of a Knowledge Graph statement. */
export interface KGSubject {
  /** URI or unique identifier for the subject. */
  id: string;
  /** Optional URI representing the type of the subject. */
  type?: string | null; // format: uri
}

/** Represents the predicate (relationship) of a Knowledge Graph statement. */
export interface KGPredicate {
  /** URI representing the type of the predicate/relationship. */
  id: string; // format: uri
}

/** Base for KGObject. Do not use directly. */
interface KGObjectBase {
  /** URI or unique identifier if the object is a resource/node. */
  id?: string | null; // format: uri
  /** The literal value if the object is an attribute. */
  value?: string | number | boolean | null;
  /** Optional URI for object type or literal datatype. */
  type?: string | null; // format: uri
}
/** KG Object representing a resource/node. */
export type KGObjectResource = KGObjectBase & { id: string; value?: never };
/** KG Object representing a literal value. */
export type KGObjectLiteral = KGObjectBase & { value: string | number | boolean; id?: never };
/** Represents the object of a KG statement (resource or literal). */
export type KGObject = KGObjectResource | KGObjectLiteral;

/** Represents a single Knowledge Graph statement (triple). */
export interface KGStatement {
  subject: KGSubject;
  predicate: KGPredicate;
  object: KGObject;
  /** Optional named graph URI this statement belongs to. */
  graph?: string | null; // format: uri
  /** Optional certainty score (0.0 to 1.0). */
  certainty?: number | null; // Range [0.0, 1.0]
  /** Optional metadata about the source or origin (e.g., source agent ID, timestamp). */
  provenance?: Record<string, unknown> | null;
}

/** Defines the type of operation in a knowledge graph patch. */
export enum PatchOperationType {
  ADD = "add",
  REMOVE = "remove",
  REPLACE = "replace",
}

/** Represents a single proposed change (add, remove, replace) to a knowledge graph. */
export interface KnowledgeGraphPatch {
  op: PatchOperationType;
  statement: KGStatement;
}

/** Parameters for the knowledge/query method. */
export interface KnowledgeQueryParams {
  /** The query string (e.g., GraphQL query). */
  query: string;
  /** Specifies the language of the query. */
  queryLanguage: "graphql"; // Currently only supporting graphql
  /** Optional dictionary of variables for the query. */
  variables?: Record<string, unknown> | null;
  /** Optional ID linking this query to a specific task. */
  taskId?: string | null;
  /** Optional ID linking this query to a specific session. */
  sessionId?: string | null;
  /** Optional minimum certainty score for results. */
  requiredCertainty?: number | null; // Range [0.0, 1.0]
  /** Optional maximum age (in seconds) for the data considered. */
  maxAgeSeconds?: number | null; // >= 0
  /** Optional metadata (e.g., auth tokens, alignment context). */
  metadata?: Record<string, unknown> | null;
}

/** Parameters for the knowledge/update method. */
export interface KnowledgeUpdateParams {
  /** A list of patch operations to apply. */
  mutations: KnowledgeGraphPatch[];
  /** Optional ID linking this update to a specific task. */
  taskId?: string | null;
  /** Optional ID linking this update to a specific session. */
  sessionId?: string | null;
  /** Optional identifier of the agent proposing the update. */
  sourceAgentId?: string | null;
  /** Optional textual justification for the proposed update. */
  justification?: string | null;
  /** Optional metadata (e.g., auth tokens, alignment context). */
  metadata?: Record<string, unknown> | null;
}

/** Parameters for the knowledge/subscribe method. */
export interface KnowledgeSubscribeParams {
  /** The query string for the subscription (e.g., GraphQL subscription). */
  subscriptionQuery: string;
  /** Specifies the language of the subscription query. */
  queryLanguage: "graphql"; // Currently only supporting graphql
  /** Optional dictionary of variables for the subscription query. */
  variables?: Record<string, unknown> | null;
  /** Optional ID linking this subscription to a specific task. */
  taskId?: string | null;
  /** Optional ID linking this subscription to a specific session. */
  sessionId?: string | null;
  /** Optional metadata (e.g., auth tokens, alignment context). */
  metadata?: Record<string, unknown> | null;
}

// === A2A Request Interfaces ===

export interface SendTaskRequest extends JSONRPCRequest {
  method: "tasks/send";
  params: TaskSendParams;
}
export interface GetTaskRequest extends JSONRPCRequest {
  method: "tasks/get";
  params: TaskQueryParams;
}
export interface CancelTaskRequest extends JSONRPCRequest {
  method: "tasks/cancel";
  params: TaskIdParams;
}
export interface SetTaskPushNotificationRequest extends JSONRPCRequest {
  method: "tasks/pushNotification/set";
  params: TaskPushNotificationConfig;
}
export interface GetTaskPushNotificationRequest extends JSONRPCRequest {
  method: "tasks/pushNotification/get";
  params: TaskIdParams;
}
export interface TaskResubscriptionRequest extends JSONRPCRequest {
  method: "tasks/resubscribe";
  params: TaskQueryParams; // Using QueryParams allows specifying history length on resubscribe
}
export interface SendTaskStreamingRequest extends JSONRPCRequest {
  method: "tasks/sendSubscribe";
  params: TaskSendParams;
}
export interface KnowledgeQueryRequest extends JSONRPCRequest {
  method: "knowledge/query";
  params: KnowledgeQueryParams;
}
export interface KnowledgeUpdateRequest extends JSONRPCRequest {
  method: "knowledge/update";
  params: KnowledgeUpdateParams;
}
export interface KnowledgeSubscribeRequest extends JSONRPCRequest {
  method: "knowledge/subscribe";
  params: KnowledgeSubscribeParams;
}

// === A2A Response Interfaces ===

export type SendTaskResponse = JSONRPCResponse<Task | null, A2AError>;
export type GetTaskResponse = JSONRPCResponse<Task | null, A2AError>;
export type CancelTaskResponse = JSONRPCResponse<Task | null, A2AError>;
export type SetTaskPushNotificationResponse = JSONRPCResponse<
  TaskPushNotificationConfig | null,
  A2AError
>;
export type GetTaskPushNotificationResponse = JSONRPCResponse<
  TaskPushNotificationConfig | null,
  A2AError
>;
export type SendTaskStreamingResponse = JSONRPCResponse<
  TaskStatusUpdateEvent | TaskArtifactUpdateEvent | null,
  A2AError
>;

// === Knowledge Response Interfaces ===

/** Result structure for a knowledge query. */
export interface KnowledgeQueryResponseResult {
  /** The query result data (GraphQL structure). */
  data?: Record<string, unknown> | unknown[] | null;
  /** Optional metadata about the query execution. */
  queryMetadata?: Record<string, unknown> | null;
}
export type KnowledgeQueryResponse = JSONRPCResponse<
  KnowledgeQueryResponseResult | null,
  A2AError
>;

/** Result structure for a knowledge update operation. */
export interface KnowledgeUpdateResponseResult {
  /** Indicates if the update was accepted/applied. */
  success: boolean;
  /** Optional count of statements affected. */
  statementsAffected?: number | null; // >= 0
  /** Optional list of URIs/IDs of created/modified entities. */
  affectedIds?: string[] | null;
  /** Optional verification status (e.g., "Verified", "Rejected"). */
  verificationStatus?: string | null;
  /** Optional details explaining verification status. */
  verificationDetails?: string | null;
}
export type KnowledgeUpdateResponse = JSONRPCResponse<
  KnowledgeUpdateResponseResult | null,
  A2AError
>;

// === Knowledge Streaming Event Interfaces ===

/** Represents a confirmed change event in the KG (for subscriptions). */
export interface KnowledgeGraphChangeEvent {
  op: PatchOperationType;
  statement: KGStatement;
  /** Unique identifier for this specific change event. */
  changeId: string; // format: uuid recommended
  /** Timestamp when the change was confirmed (ISO 8601 format). */
  timestamp: string; // format: date-time
  /** Optional metadata about the confirmed change. */
  changeMetadata?: Record<string, unknown> | null;
}

/** A single event message streamed for knowledge/subscribe. */
export type KnowledgeSubscriptionEvent = JSONRPCResponse<
  KnowledgeGraphChangeEvent | null,
  A2AError
>;

// === Error Codes and Union Type ===

/** Error code for JSON Parse Error (-32700). */
export const ErrorCodeParseError = -32700;
/** Error code for Invalid Request (-32600). */
export const ErrorCodeInvalidRequest = -32600;
/** Error code for Method Not Found (-32601). */
export const ErrorCodeMethodNotFound = -32601;
/** Error code for Invalid Params (-32602). */
export const ErrorCodeInvalidParams = -32602;
/** Error code for Internal Error (-32603). */
export const ErrorCodeInternalError = -32603;
/** Error code for Task Not Found (-32001). */
export const ErrorCodeTaskNotFound = -32001;
/** Error code for Task Not Cancelable (-32002). */
export const ErrorCodeTaskNotCancelable = -32002;
/** Error code for Push Notification Not Supported (-32003). */
export const ErrorCodePushNotificationNotSupported = -32003;
/** Error code for Unsupported Operation (-32004). */
export const ErrorCodeUnsupportedOperation = -32004;
/** Error code for Incompatible Content Types (-32005). */
export const ErrorCodeContentTypeNotSupported = -32005;
/** Error code for Knowledge Query Error (-32010). */
export const ErrorCodeKnowledgeQueryError = -32010;
/** Error code for Knowledge Update Error (-32011). */
export const ErrorCodeKnowledgeUpdateError = -32011;
/** Error code for Knowledge Subscription Error (-32012). */
export const ErrorCodeKnowledgeSubscriptionError = -32012;
/** Error code for Alignment Violation Error (-32013). */
export const ErrorCodeAlignmentViolationError = -32013;

/** Union of all well-known A2A error codes defined in this schema. */
export type KnownErrorCode =
  | typeof ErrorCodeParseError
  | typeof ErrorCodeInvalidRequest
  | typeof ErrorCodeMethodNotFound
  | typeof ErrorCodeInvalidParams
  | typeof ErrorCodeInternalError
  | typeof ErrorCodeTaskNotFound
  | typeof ErrorCodeTaskNotCancelable
  | typeof ErrorCodePushNotificationNotSupported
  | typeof ErrorCodeUnsupportedOperation
  | typeof ErrorCodeContentTypeNotSupported
  | typeof ErrorCodeKnowledgeQueryError
  | typeof ErrorCodeKnowledgeUpdateError
  | typeof ErrorCodeKnowledgeSubscriptionError
  | typeof ErrorCodeAlignmentViolationError;

/** Generic A2A Error type using known codes or number. */
export type A2AError = JSONRPCError<unknown | null, KnownErrorCode | number>;

// === Union Types for A2A Requests/Responses ===

/** Represents any valid request defined in the A2A protocol. */
export type A2ARequest =
  | SendTaskRequest
  | GetTaskRequest
  | CancelTaskRequest
  | SetTaskPushNotificationRequest
  | GetTaskPushNotificationRequest
  | TaskResubscriptionRequest
  | SendTaskStreamingRequest
  | KnowledgeQueryRequest
  | KnowledgeUpdateRequest
  | KnowledgeSubscribeRequest;

/** Represents any valid non-streaming JSON-RPC response defined in the A2A protocol. */
export type A2AResponse =
  | SendTaskResponse
  | GetTaskResponse
  | CancelTaskResponse
  | SetTaskPushNotificationResponse
  | GetTaskPushNotificationResponse
  | KnowledgeQueryResponse
  | KnowledgeUpdateResponse;
// Streaming responses use SendTaskStreamingResponse or KnowledgeSubscriptionEvent formats over SSE.
