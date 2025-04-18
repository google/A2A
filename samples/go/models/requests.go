package models

// TaskSendParams represents the parameters for sending a task message
type TaskSendParams struct {
	// ID is the unique identifier for the task being initiated or continued
	ID string `json:"id"`
	// SessionID is an optional identifier for the session this task belongs to
	SessionID *string `json:"sessionId,omitempty"`
	// Message is the message content to send to the agent for processing
	Message Message `json:"message"`
	// PushNotification is optional push notification information for receiving notifications
	PushNotification *PushNotificationConfig `json:"pushNotification,omitempty"`
	// HistoryLength is an optional parameter to specify how much message history to include
	HistoryLength *int `json:"historyLength,omitempty"`
	// Metadata is optional metadata associated with sending this message
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// TaskIDParams represents the base parameters for task ID-based operations
type TaskIDParams struct {
	// ID is the unique identifier of the task
	ID string `json:"id"`
	// Metadata is optional metadata to include with the operation
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// TaskQueryParams represents the parameters for querying task information
type TaskQueryParams struct {
	TaskIDParams
	// HistoryLength is an optional parameter to specify how much history to retrieve
	HistoryLength *int `json:"historyLength,omitempty"`
}

// PushNotificationConfig represents the configuration for push notifications
type PushNotificationConfig struct {
	// URL is the endpoint where the agent should send notifications
	URL string `json:"url"`
	// Token is a token to be included in push notification requests for verification
	Token *string `json:"token,omitempty"`
	// Authentication is optional authentication details needed by the agent
	Authentication *AgentAuthentication `json:"authentication,omitempty"`
}

// TaskPushNotificationConfig represents the configuration for task-specific push notifications
type TaskPushNotificationConfig struct {
	// ID is the ID of the task the notification config is associated with
	ID string `json:"id"`
	// PushNotificationConfig is the push notification configuration details
	PushNotificationConfig PushNotificationConfig `json:"pushNotificationConfig"`
}

// SendTaskRequest represents a request to send a task message
type SendTaskRequest struct {
	JSONRPCRequest
	Method string         `json:"method"`
	Params TaskSendParams `json:"params"`
}

// GetTaskRequest represents a request to get task status
type GetTaskRequest struct {
	JSONRPCRequest
	Method string          `json:"method"`
	Params TaskQueryParams `json:"params"`
}

// CancelTaskRequest represents a request to cancel a task
type CancelTaskRequest struct {
	JSONRPCRequest
	Method string       `json:"method"`
	Params TaskIDParams `json:"params"`
}

// SetTaskPushNotificationRequest represents a request to set task notifications
type SetTaskPushNotificationRequest struct {
	JSONRPCRequest
	Method string                     `json:"method"`
	Params TaskPushNotificationConfig `json:"params"`
}

// GetTaskPushNotificationRequest represents a request to get task notification configuration
type GetTaskPushNotificationRequest struct {
	JSONRPCRequest
	Method string       `json:"method"`
	Params TaskIDParams `json:"params"`
}

// TaskResubscriptionRequest represents a request to resubscribe to task updates
type TaskResubscriptionRequest struct {
	JSONRPCRequest
	Method string          `json:"method"`
	Params TaskQueryParams `json:"params"`
}

// SendTaskStreamingRequest represents a request to send a task message and subscribe to updates
type SendTaskStreamingRequest struct {
	JSONRPCRequest
	Method string         `json:"method"`
	Params TaskSendParams `json:"params"`
}
