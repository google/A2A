/**
 * @title A2A
 */

// --8<-- [start:AgentProvider]
/**
 * Represents the service provider of an agent.
 */
export interface AgentProvider {
  /** Agent provider's organization name. */
  organization: string;
  /** Agent provider's URL. */
  url: string;
}
// --8<-- [end:AgentProvider]

// --8<-- [start:AgentCapabilities]
/**
 * Defines optional capabilities supported by an agent.
 */
export interface AgentCapabilities {
  /** true if the agent supports SSE. */
  streaming?: boolean;
  /** true if the agent can notify updates to client. */
  pushNotifications?: boolean;
  /** true if the agent exposes status change history for tasks. */
  stateTransitionHistory?: boolean;
  /** extensions supported by this agent. */
  extensions?: AgentExtension[];
}
// --8<-- [end:AgentCapabilities]

// --8<-- [start:AgentExtension]
/**
 * A declaration of an extension supported by an Agent.
 */
export interface AgentExtension {
  /** The URI of the extension. */
  uri: string;
  /** A description of how this agent uses this extension. */
  description?: string;
  /** Whether the client must follow specific requirements of the extension. */
  required?: boolean;
  /** Optional configuration for the extension. */
  params?: { [key: string]: any };
}
// --8<-- [end:AgentExtension]

// --8<-- [start:AgentSkill]
/**
 * Represents a unit of capability that an agent can perform.
 */
export interface AgentSkill {
  /** Unique identifier for the agent's skill. */
  id: string;
  /** Human readable name of the skill. */
  name: string;
  /**
   * Description of the skill - will be used by the client or a human
   * as a hint to understand what the skill does.
   */
  description: string;
  /**
   * Set of tagwords describing classes of capabilities for this specific skill.
   * @example ["cooking", "customer support", "billing"]
   */
  tags: string[];
  /**
   * The set of example scenarios that the skill can perform.
   * Will be used by the client as a hint to understand how the skill can be used.
   * @example ["I need a recipe for bread"]
   */
  examples?: string[]; // example prompts for tasks
  /**
   * The set of interaction modes that the skill supports
   * (if different than the default).
   * Supported media types for input.
   */
  inputModes?: string[];
  /** Supported media types for output. */
  outputModes?: string[];
}
// --8<-- [end:AgentSkill]

// --8<-- [start:AgentCard]
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
  /** A URL to an icon for the agent. */
  iconUrl?: string;
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
  /** Security scheme details used for authenticating with this agent. */
  securitySchemes?: { [scheme: string]: SecurityScheme };
  /** Security requirements for contacting the agent. */
  security?: { [scheme: string]: string[] }[];
  /**
   * The set of interaction modes that the agent supports across all skills. This can be overridden per-skill.
   * Supported media types for input.
   */
  defaultInputModes: string[];
  /** Supported media types for output. */
  defaultOutputModes: string[];
  /** Skills are a unit of capability that an agent can perform. */
  skills: AgentSkill[];
  /**
   * true if the agent supports providing an extended agent card when the user is authenticated.
   * Defaults to false if not specified.
   */
  supportsAuthenticatedExtendedCard?: boolean;
}
// --8<-- [end:AgentCard]

// --8<-- [start:Task]
export interface Task {
  /** Unique identifier for the task */
  id: string;
  /** Server-generated id for contextual alignment across interactions */
  contextId: string;
  /** Current status of the task */
  status: TaskStatus;
  history?: Message[];
  /** Collection of artifacts created by the agent. */
  artifacts?: Artifact[];
  /** Extension metadata. */
  metadata?: {
    [key: string]: any;
  };
  /** Event type */
  kind: "task";
}
// --8<-- [end:Task]

// --8<-- [start:TaskStatus]
/** TaskState and accompanying message. */
export interface TaskStatus {
  state: TaskState;
  /** Additional status updates for client */
  message?: Message;
  /**
   * ISO 8601 datetime string when the status was recorded.
   * @example "2023-10-27T10:00:00Z"
   * */
  timestamp?: string;
}
// --8<-- [end:TaskStatus]

// --8<-- [start:TaskStatusUpdateEvent]
/** Sent by server during sendStream or subscribe requests */
export interface TaskStatusUpdateEvent {
  /** Task id */
  taskId: string;
  /** The context the task is associated with */
  contextId: string;
  /** Event type */
  kind: "status-update";
  /** Current status of the task */
  status: TaskStatus;
  /** Indicates the end of the event stream */
  final: boolean;
  /** Extension metadata. */
  metadata?: {
    [key: string]: any;
  };
}
// --8<-- [end:TaskStatusUpdateEvent]

// --8<-- [start:TaskArtifactUpdateEvent]
/** Sent by server during sendStream or subscribe requests */
export interface TaskArtifactUpdateEvent {
  /** Task id */
  taskId: string;
  /** The context the task is associated with */
  contextId: string;
  /** Event type */
  kind: "artifact-update";
  /** Generated artifact */
  artifact: Artifact;
  /** Indicates if this artifact appends to a previous one */
  append?: boolean;
  /** Indicates if this is the last chunk of the artifact */
  lastChunk?: boolean;
  /** Extension metadata. */
  metadata?: {
    [key: string]: any;
  };
}
// --8<-- [end:TaskArtifactUpdateEvent]

// --8<-- [start:TaskIdParams]
/** Parameters containing only a task ID, used for simple task operations. */
export interface TaskIdParams {
  /** Task id. */
  id: string;
  metadata?: {
    [key: string]: any;
  };
}
// --8<-- [end:TaskIdParams]

// --8<-- [start:TaskQueryParams]
/** Parameters for querying a task, including optional history length. */
export interface TaskQueryParams extends TaskIdParams {
  /** Number of recent messages to be retrieved. */
  historyLength?: number;
}
// --8<-- [end:TaskQueryParams]

// --8<-- [start:MessageSendConfiguration]
/**Configuration for the send message request. */
export interface MessageSendConfiguration {
  /** Accepted output modalities by the client. */
  acceptedOutputModes: string[];
  /** Number of recent messages to be retrieved. */
  historyLength?: number;
  /** Where the server should send notifications when disconnected. */
  pushNotificationConfig?: PushNotificationConfig;
  /** If the server should treat the client as a blocking request. */
  blocking?: boolean;
}
// --8<-- [end:MessageSendConfiguration]

// --8<-- [start:MessageSendParams]
/** Sent by the client to the agent as a request. May create, continue or restart a task. */
export interface MessageSendParams {
  /** The message being sent to the server. */
  message: Message;
  /** Send message configuration. */
  configuration?: MessageSendConfiguration;
  /** Extension metadata. */
  metadata?: {
    [key: string]: any;
  };
}
// --8<-- [end:MessageSendParams]

// --8<-- [start:TaskState]
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
// --8<-- [end:TaskState]

// --8<-- [start:Artifact]
/** Represents an artifact generated for a task. */
export interface Artifact {
  /** Unique identifier for the artifact. */
  artifactId: string;
  /** Optional name for the artifact. */
  name?: string;
  /** Optional description for the artifact. */
  description?: string;
  /** Artifact parts. */
  parts: Part[];
  /** Extension metadata. */
  metadata?: {
    [key: string]: any;
  };
  /** The URIs of extensions that are present or contributed to this Artifact. */
  extensions?: string[];
}
// --8<-- [end:Artifact]

// --8<-- [start:Message]
/** Represents a single message exchanged between user and agent. */
export interface Message {
  /** Message sender's role */
  role: "user" | "agent";
  /** Message content */
  parts: Part[];
  /** Extension metadata. */
  metadata?: {
    [key: string]: any;
  };
  /** The URIs of extensions that are present or contributed to this Message. */
  extensions?: string[];
  /** List of tasks referenced as context by this message.*/
  referenceTaskIds?: string[];
  /** Identifier created by the message creator*/
  messageId: string;
  /** Identifier of task the message is related to */
  taskId?: string;
  /** The context the message is associated with */
  contextId?: string;
  /** Event type */
  kind: "message";
}
// --8<-- [end:Message]

// --8<-- [start:PartBase]
/** Base properties common to all message parts. */
export interface PartBase {
  /** Optional metadata associated with the part. */
  metadata?: {
    [key: string]: any;
  };
}
// --8<-- [end:PartBase]

// --8<-- [start:TextPart]
/** Represents a text segment within parts.*/
export interface TextPart extends PartBase {
  /** Part type - text for TextParts*/
  kind: "text";
  /** Text content */
  text: string;
}
// --8<-- [end:TextPart]

// --8<-- [start:FileBase]
/** Represents the base entity for FileParts */
export interface FileBase {
  /** Optional name for the file */
  name?: string;
  /** Optional mimeType for the file */
  mimeType?: string;
}
// --8<-- [end:FileBase]

// --8<-- [start:FileWithBytes]
/** Define the variant where 'bytes' is present and 'uri' is absent */
export interface FileWithBytes extends FileBase {
  /** base64 encoded content of the file*/
  bytes: string;
  uri?: never;
}
// --8<-- [end:FileWithBytes]

// --8<-- [start:FileWithUri]
/** Define the variant where 'uri' is present and 'bytes' is absent  */
export interface FileWithUri extends FileBase {
  /** URL for the File content */
  uri: string;
  bytes?: never;
}
// --8<-- [end:FileWithUri]

// --8<-- [start:FilePart]
/** Represents a File segment within parts.*/
export interface FilePart extends PartBase {
  /** Part type - file for FileParts */
  kind: "file";
  /** File content either as url or bytes */
  file: FileWithBytes | FileWithUri;
}
// --8<-- [end:FilePart]

// --8<-- [start:DataPart]
/** Represents a structured data segment within a message part. */
export interface DataPart extends PartBase {
  /** Part type - data for DataParts */
  kind: "data";
  /** Structured data content
   */
  data: {
    [key: string]: any;
  };
}
// --8<-- [end:DataPart]

// --8<-- [start:Part]
/** Represents a part of a message, which can be text, a file, or structured data. */
export type Part = TextPart | FilePart | DataPart;
// --8<-- [end:Part]

// --8<-- [start:PushNotificationAuthenticationInfo]
/** Defines authentication details for push notifications. */
export interface PushNotificationAuthenticationInfo {
  /** Supported authentication schemes - e.g. Basic, Bearer */
  schemes: string[];
  /** Optional credentials */
  credentials?: string;
}
// --8<-- [end:PushNotificationAuthenticationInfo]

// --8<-- [start:PushNotificationConfig]
/**Configuration for setting up push notifications for task updates. */
export interface PushNotificationConfig {
  /** Push Notification ID - created by server to support multiple callbacks */
  id?: string;
  /** URL for sending the push notifications. */
  url: string;
  /** Token unique to this task/session. */
  token?: string;
  authentication?: PushNotificationAuthenticationInfo;
}
// --8<-- [end:PushNotificationConfig]

// --8<-- [start:TaskPushNotificationConfig]
/**Parameters for setting or getting push notification configuration for a task */
export interface TaskPushNotificationConfig {
  /** Task id. */
  taskId: string;
  /** Push notification configuration. */
  pushNotificationConfig: PushNotificationConfig;
}
// --8<-- [end:TaskPushNotificationConfig]

// --8<-- [start:SecurityScheme]
/**
 * Mirrors the OpenAPI Security Scheme Object
 * (https://swagger.io/specification/#security-scheme-object)
 */
export type SecurityScheme =
  | APIKeySecurityScheme
  | HTTPAuthSecurityScheme
  | OAuth2SecurityScheme
  | OpenIdConnectSecurityScheme;
// --8<-- [end:SecurityScheme]

// --8<-- [start:SecuritySchemeBase]
/** Base properties shared by all security schemes. */
export interface SecuritySchemeBase {
  /** Description of this security scheme. */
  description?: string;
}
// --8<-- [end:SecuritySchemeBase]

// --8<-- [start:APIKeySecurityScheme]
/** API Key security scheme. */
export interface APIKeySecurityScheme extends SecuritySchemeBase {
  type: "apiKey";
  /** The location of the API key. Valid values are "query", "header", or "cookie".  */
  in: "query" | "header" | "cookie";
  /** The name of the header, query or cookie parameter to be used. */
  name: string;
}
// --8<-- [end:APIKeySecurityScheme]

// --8<-- [start:HTTPAuthSecurityScheme]
/** HTTP Authentication security scheme. */
export interface HTTPAuthSecurityScheme extends SecuritySchemeBase {
  type: "http";
  /**
   * The name of the HTTP Authentication scheme to be used in the Authorization header as defined
   * in RFC7235. The values used SHOULD be registered in the IANA Authentication Scheme registry.
   * The value is case-insensitive, as defined in RFC7235.
   */
  scheme: string;
  /**
   * A hint to the client to identify how the bearer token is formatted. Bearer tokens are usually
   * generated by an authorization server, so this information is primarily for documentation
   * purposes.
   */
  bearerFormat?: string;
}
// --8<-- [end:HTTPAuthSecurityScheme]

// --8<-- [start:OAuth2SecurityScheme]
/** OAuth2.0 security scheme configuration. */
export interface OAuth2SecurityScheme extends SecuritySchemeBase {
  type: "oauth2";
  /** An object containing configuration information for the flow types supported. */
  flows: OAuthFlows;
}
// --8<-- [end:OAuth2SecurityScheme]

// --8<-- [start:OpenIdConnectSecurityScheme]
/** OpenID Connect security scheme configuration. */
export interface OpenIdConnectSecurityScheme extends SecuritySchemeBase {
  type: "openIdConnect";
  /** Well-known URL to discover the [[OpenID-Connect-Discovery]] provider metadata. */
  openIdConnectUrl: string;
}
// --8<-- [end:OpenIdConnectSecurityScheme]

// --8<-- [start:OAuthFlows]
/** Allows configuration of the supported OAuth Flows */
export interface OAuthFlows {
  /** Configuration for the OAuth Authorization Code flow. Previously called accessCode in OpenAPI 2.0. */
  authorizationCode?: AuthorizationCodeOAuthFlow;
  /** Configuration for the OAuth Client Credentials flow. Previously called application in OpenAPI 2.0 */
  clientCredentials?: ClientCredentialsOAuthFlow;
  /** Configuration for the OAuth Implicit flow */
  implicit?: ImplicitOAuthFlow;
  /** Configuration for the OAuth Resource Owner Password flow */
  password?: PasswordOAuthFlow;
}
// --8<-- [end:OAuthFlows]

// --8<-- [start:AuthorizationCodeOAuthFlow]
/** Configuration details for a supported OAuth Flow */
export interface AuthorizationCodeOAuthFlow {
  /**
   * The authorization URL to be used for this flow. This MUST be in the form of a URL. The OAuth2
   * standard requires the use of TLS
   */
  authorizationUrl: string;
  /**
   * The token URL to be used for this flow. This MUST be in the form of a URL. The OAuth2 standard
   * requires the use of TLS.
   */
  tokenUrl: string;
  /**
   * The URL to be used for obtaining refresh tokens. This MUST be in the form of a URL. The OAuth2
   * standard requires the use of TLS.
   */
  refreshUrl?: string;
  /**
   * The available scopes for the OAuth2 security scheme. A map between the scope name and a short
   * description for it. The map MAY be empty.
   */
  scopes: { [name: string]: string };
}
// --8<-- [end:AuthorizationCodeOAuthFlow]

// --8<-- [start:ClientCredentialsOAuthFlow]
/** Configuration details for a supported OAuth Flow */
export interface ClientCredentialsOAuthFlow {
  /**
   * The token URL to be used for this flow. This MUST be in the form of a URL. The OAuth2 standard
   * requires the use of TLS.
   */
  tokenUrl: string;
  /**
   * The URL to be used for obtaining refresh tokens. This MUST be in the form of a URL. The OAuth2
   * standard requires the use of TLS.
   */
  refreshUrl?: string;
  /**
   * The available scopes for the OAuth2 security scheme. A map between the scope name and a short
   * description for it. The map MAY be empty.
   */
  scopes: { [name: string]: string };
}
// --8<-- [end:ClientCredentialsOAuthFlow]

// --8<-- [start:ImplicitOAuthFlow]
/** Configuration details for a supported OAuth Flow */
export interface ImplicitOAuthFlow {
  /**
   * The authorization URL to be used for this flow. This MUST be in the form of a URL. The OAuth2
   * standard requires the use of TLS
   */
  authorizationUrl: string;
  /**
   * The URL to be used for obtaining refresh tokens. This MUST be in the form of a URL. The OAuth2
   * standard requires the use of TLS.
   */
  refreshUrl?: string;
  /**
   * The available scopes for the OAuth2 security scheme. A map between the scope name and a short
   * description for it. The map MAY be empty.
   */
  scopes: { [name: string]: string };
}
// --8<-- [end:ImplicitOAuthFlow]

// --8<-- [start:PasswordOAuthFlow]
/** Configuration details for a supported OAuth Flow */
export interface PasswordOAuthFlow {
  /**
   * The token URL to be used for this flow. This MUST be in the form of a URL. The OAuth2 standard
   * requires the use of TLS.
   */
  tokenUrl: string;
  /**
   * The URL to be used for obtaining refresh tokens. This MUST be in the form of a URL. The OAuth2
   * standard requires the use of TLS.
   */
  refreshUrl?: string;
  /**
   * The available scopes for the OAuth2 security scheme. A map between the scope name and a short
   * description for it. The map MAY be empty.
   */
  scopes: { [name: string]: string };
}
// --8<-- [end:PasswordOAuthFlow]

// --8<-- [start:JSONRPCMessage]
/**
 * Base interface for any JSON-RPC 2.0 request or response.
 */
export interface JSONRPCMessage {
  /**
   * Specifies the version of the JSON-RPC protocol. MUST be exactly "2.0".
   */
  readonly jsonrpc: "2.0";

  /**
   * An identifier established by the Client that MUST contain a String, Number.
   * Numbers SHOULD NOT contain fractional parts.
   * @nullable true
   */
  id?: number | string | null;
}
// --8<-- [end:JSONRPCMessage]

// --8<-- [start:JSONRPCRequest]
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
// --8<-- [end:JSONRPCRequest]

// --8<-- [start:JSONRPCError]
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
// --8<-- [end:JSONRPCError]

// --8<-- [start:JSONRPCResult]
/**
 * Represents a JSON-RPC 2.0 Success Response object.
 */
export interface JSONRPCSuccessResponse extends JSONRPCMessage {
  /**
   * @nullable true
   */
  id: number | string | null;
  /**
   * The result object on success
   */
  result: any;

  error?: never; // Optional 'never' helps enforce exclusivity
}
// --8<-- [end:JSONRPCResult]

// --8<-- [start:JSONRPCErrorResponse]
/**
 * Represents a JSON-RPC 2.0 Error Response object.
 */
export interface JSONRPCErrorResponse extends JSONRPCMessage {
  /**
   * @nullable true
   */
  id: number | string | null;
  result?: never; // Optional 'never' helps enforce exclusivity
  error: JSONRPCError | A2AError;
}
// --8<-- [end:JSONRPCErrorResponse]

// --8<-- [start:JSONRPCResponse]
/**
 * Represents a JSON-RPC 2.0 Response object.
 */
export type JSONRPCResponse =
  | SendMessageResponse
  | SendStreamingMessageResponse
  | GetTaskResponse
  | CancelTaskResponse
  | SetTaskPushNotificationConfigResponse
  | GetTaskPushNotificationConfigResponse;
// --8<-- [end:JSONRPCResponse]

// --8<-- [start:SendMessageRequest]
/**
 * JSON-RPC request model for the 'message/send' method.
 */
export interface SendMessageRequest extends JSONRPCRequest {
  id: number | string;
  method: "message/send";
  params: MessageSendParams;
}
// --8<-- [end:SendMessageRequest]

// --8<-- [start:SendMessageSuccessResponse]
/**
 * JSON-RPC success response model for the 'message/send' method.
 */
export interface SendMessageSuccessResponse extends JSONRPCSuccessResponse {
  result: Message | Task;
}
// --8<-- [end:SendMessageSuccessResponse]

// --8<-- [start:SendMessageResponse]
/**
 * JSON-RPC response model for the 'message/send' method.
 */
export type SendMessageResponse =
  | SendMessageSuccessResponse
  | JSONRPCErrorResponse;
// --8<-- [end:SendMessageResponse]

// --8<-- [start:SendStreamingMessageRequest]
/**
 * JSON-RPC request model for the 'message/stream' method.
 */
export interface SendStreamingMessageRequest extends JSONRPCRequest {
  id: number | string;
  method: "message/stream";
  params: MessageSendParams;
}
// --8<-- [end:SendStreamingMessageRequest]

// --8<-- [start:SendStreamingMessageSuccessResponse]
/**
 * JSON-RPC success response model for the 'message/stream' method.
 */
export interface SendStreamingMessageSuccessResponse
  extends JSONRPCSuccessResponse {
  result: Message | Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent;
}
// --8<-- [end:SendStreamingMessageSuccessResponse]

// --8<-- [start:SendStreamingMessageResponse]
/**
 * JSON-RPC response model for the 'message/stream' method.
 */
export type SendStreamingMessageResponse =
  | SendStreamingMessageSuccessResponse
  | JSONRPCErrorResponse;
// --8<-- [end:SendStreamingMessageResponse]

// --8<-- [start:GetTaskRequest]
/**
 * JSON-RPC request model for the 'tasks/get' method.
 */
export interface GetTaskRequest extends JSONRPCRequest {
  id: number | string;
  /** A String containing the name of the method to be invoked. */
  method: "tasks/get";
  /** A Structured value that holds the parameter values to be used during the invocation of the method. */
  params: TaskQueryParams;
}
// --8<-- [end:GetTaskRequest]

// --8<-- [start:GetTaskSuccessResponse]
/**
 * JSON-RPC success response for the 'tasks/get' method.
 */
export interface GetTaskSuccessResponse extends JSONRPCSuccessResponse {
  /** The result object on success. */
  result: Task;
}
// --8<-- [end:GetTaskSuccessResponse]

// --8<-- [start:GetTaskResponse]
/**
 * JSON-RPC response for the 'tasks/get' method.
 */
export type GetTaskResponse = GetTaskSuccessResponse | JSONRPCErrorResponse;
// --8<-- [end:GetTaskResponse]

// --8<-- [start:CancelTaskRequest]
/**
 * JSON-RPC request model for the 'tasks/cancel' method.
 */
export interface CancelTaskRequest extends JSONRPCRequest {
  id: number | string;
  /** A String containing the name of the method to be invoked. */
  method: "tasks/cancel";
  /** A Structured value that holds the parameter values to be used during the invocation of the method. */
  params: TaskIdParams;
}
// --8<-- [end:CancelTaskRequest]

// --8<-- [start:CancelTaskSuccessResponse]
/**
 * JSON-RPC success response model for the 'tasks/cancel' method.
 */
export interface CancelTaskSuccessResponse extends JSONRPCSuccessResponse {
  /** The result object on success. */
  result: Task;
}
// --8<-- [end:CancelTaskSuccessResponse]

// --8<-- [start:CancelTaskResponse]
/**
 * JSON-RPC response for the 'tasks/cancel' method.
 */
export type CancelTaskResponse =
  | CancelTaskSuccessResponse
  | JSONRPCErrorResponse;
// --8<-- [end:CancelTaskResponse]

// --8<-- [start:SetTaskPushNotificationConfigRequest]
/**
 * JSON-RPC request model for the 'tasks/pushNotificationConfig/set' method.
 */
export interface SetTaskPushNotificationConfigRequest extends JSONRPCRequest {
  id: number | string;
  /** A String containing the name of the method to be invoked. */
  method: "tasks/pushNotificationConfig/set";
  /** A Structured value that holds the parameter values to be used during the invocation of the method. */
  params: TaskPushNotificationConfig;
}
// --8<-- [end:SetTaskPushNotificationConfigRequest]

// --8<-- [start:SetTaskPushNotificationConfigSuccessResponse]
/**
 * JSON-RPC success response model for the 'tasks/pushNotificationConfig/set' method.
 */
export interface SetTaskPushNotificationConfigSuccessResponse
  extends JSONRPCSuccessResponse {
  /** The result object on success. */
  result: TaskPushNotificationConfig;
}
// --8<-- [end:SetTaskPushNotificationConfigSuccessResponse]

// --8<-- [start:SetTaskPushNotificationConfigResponse]
/**
 * JSON-RPC response for the 'tasks/pushNotificationConfig/set' method.
 */
export type SetTaskPushNotificationConfigResponse =
  | SetTaskPushNotificationConfigSuccessResponse
  | JSONRPCErrorResponse;
// --8<-- [end:SetTaskPushNotificationConfigResponse]

// --8<-- [start:GetTaskPushNotificationConfigRequest]
/**
 * JSON-RPC request model for the 'tasks/pushNotificationConfig/get' method.
 */
export interface GetTaskPushNotificationConfigRequest extends JSONRPCRequest {
  id: number | string;
  /** A String containing the name of the method to be invoked. */
  method: "tasks/pushNotificationConfig/get";
  /** A Structured value that holds the parameter values to be used during the invocation of the method. */
  params: TaskIdParams;
}
// --8<-- [end:GetTaskPushNotificationConfigRequest]

// --8<-- [start:GetTaskPushNotificationConfigSuccessResponse]
/**
 * JSON-RPC success response model for the 'tasks/pushNotificationConfig/get' method.
 */
export interface GetTaskPushNotificationConfigSuccessResponse
  extends JSONRPCSuccessResponse {
  /** The result object on success. */
  result: TaskPushNotificationConfig;
}
// --8<-- [end:GetTaskPushNotificationConfigSuccessResponse]

// --8<-- [start:GetTaskPushNotificationConfigResponse]
/**
 * JSON-RPC response for the 'tasks/pushNotificationConfig/set' method.
 */
export type GetTaskPushNotificationConfigResponse =
  | GetTaskPushNotificationConfigSuccessResponse
  | JSONRPCErrorResponse;
// --8<-- [end:GetTaskPushNotificationConfigResponse]

// --8<-- [start:TaskResubscriptionRequest]
/**
 * JSON-RPC request model for the 'tasks/resubscribe' method.
 */
export interface TaskResubscriptionRequest extends JSONRPCRequest {
  id: number | string;
  /** A String containing the name of the method to be invoked. */
  method: "tasks/resubscribe";
  /** A Structured value that holds the parameter values to be used during the invocation of the method. */
  params: TaskIdParams;
}
// --8<-- [end:TaskResubscriptionRequest]

// --8<-- [start:A2ARequest]
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
// --8<-- [end:A2ARequest]

// --8<-- [start:JSONParseError]
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
// --8<-- [end:JSONParseError]

// --8<-- [start:InvalidRequestError]
/**
 * JSON-RPC error indicating the JSON sent is not a valid Request object.
 */
export interface InvalidRequestError extends JSONRPCError {
  /** A Number that indicates the error type that occurred. */
  code: -32600;
  /**
   * @default Request payload validation error
   */
  message: string;
}
// --8<-- [end:InvalidRequestError]

// --8<-- [start:MethodNotFoundError]
/**
 * JSON-RPC error indicating the method does not exist or is not available.
 */
export interface MethodNotFoundError extends JSONRPCError {
  /** A Number that indicates the error type that occurred. */
  code: -32601;
  /**
   * @default Method not found
   */
  message: string;
}
// --8<-- [end:MethodNotFoundError]

// --8<-- [start:InvalidParamsError]
/**
 * JSON-RPC error indicating invalid method parameter(s).
 */
export interface InvalidParamsError extends JSONRPCError {
  /** A Number that indicates the error type that occurred. */
  code: -32602;
  /**
   * @default Invalid parameters
   */
  message: string;
}
// --8<-- [end:InvalidParamsError]

// --8<-- [start:InternalError]
/**
 * JSON-RPC error indicating an internal JSON-RPC error on the server.
 */
export interface InternalError extends JSONRPCError {
  /** A Number that indicates the error type that occurred. */
  code: -32603;
  /**
   * @default Internal error
   */
  message: string;
}
// --8<-- [end:InternalError]

// --8<-- [start:TaskNotFoundError]
/**
 * A2A specific error indicating the requested task ID was not found.
 */
export interface TaskNotFoundError extends JSONRPCError {
  /** A Number that indicates the error type that occurred. */
  code: -32001;
  /**
   * @default Task not found
   */
  message: string;
}
// --8<-- [end:TaskNotFoundError]

// --8<-- [start:TaskNotCancelableError]
/**
 * A2A specific error indicating the task is in a state where it cannot be canceled.
 */
export interface TaskNotCancelableError extends JSONRPCError {
  /** A Number that indicates the error type that occurred. */
  code: -32002;
  /**
   * @default Task cannot be canceled
   */
  message: string;
}
// --8<-- [end:TaskNotCancelableError]

// --8<-- [start:PushNotificationNotSupportedError]
/**
 * A2A specific error indicating the agent does not support push notifications.
 */
export interface PushNotificationNotSupportedError extends JSONRPCError {
  /** A Number that indicates the error type that occurred. */
  code: -32003;
  /**
   * @default Push Notification is not supported
   */
  message: string;
}
// --8<-- [end:PushNotificationNotSupportedError]

// --8<-- [start:UnsupportedOperationError]
/**
 * A2A specific error indicating the requested operation is not supported by the agent.
 */
export interface UnsupportedOperationError extends JSONRPCError {
  /** A Number that indicates the error type that occurred. */
  code: -32004;
  /**
   * @default This operation is not supported
   */
  message: string;
}
// --8<-- [end:UnsupportedOperationError]

// --8<-- [start:ContentTypeNotSupportedError]
/**
 * A2A specific error indicating incompatible content types between request and agent capabilities.
 */
export interface ContentTypeNotSupportedError extends JSONRPCError {
  /** A Number that indicates the error type that occurred. */
  code: -32005;
  /**
   * @default Incompatible content types
   */
  message: string;
}
// --8<-- [end:ContentTypeNotSupportedError]

// --8<-- [start:InvalidAgentResponseError]
/**
 * A2A specific error indicating agent returned invalid response for the current method
 */
export interface InvalidAgentResponseError extends JSONRPCError {
  /** A Number that indicates the error type that occurred. */
  code: -32006;
  /**
   * @default Invalid agent response
   */
  message: string;
}
// --8<-- [end:InvalidAgentResponseError]

// --8<-- [start:A2AError]
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
// --8<-- [end:A2AError]
