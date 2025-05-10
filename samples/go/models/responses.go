package models

// ErrorCode represents the error codes used in the A2A protocol
type ErrorCode int

const (
	ErrorCodeParseError                   ErrorCode = -32700
	ErrorCodeInvalidRequest               ErrorCode = -32600
	ErrorCodeMethodNotFound               ErrorCode = -32601
	ErrorCodeInvalidParams                ErrorCode = -32602
	ErrorCodeInternalError                ErrorCode = -32603
	ErrorCodeTaskNotFound                 ErrorCode = -32000
	ErrorCodeTaskNotCancelable            ErrorCode = -32001
	ErrorCodePushNotificationNotSupported ErrorCode = -32002
	ErrorCodeUnsupportedOperation         ErrorCode = -32003
)

// A2AError represents an error in the A2A protocol
type A2AError struct {
	JSONRPCError
	Code ErrorCode `json:"code"`
}

// SendTaskResponse represents a response to a send task request
type SendTaskResponse struct {
	JSONRPCResponse
	Result *Task     `json:"result,omitempty"`
	Error  *A2AError `json:"error,omitempty"`
}

// SendTaskStreamingResponse represents a response to a streaming task request
type SendTaskStreamingResponse struct {
	JSONRPCResponse
	Result interface{} `json:"result,omitempty"` // Can be TaskStatusUpdateEvent or TaskArtifactUpdateEvent
	Error  *A2AError   `json:"error,omitempty"`
}

// GetTaskResponse represents a response to a get task request
type GetTaskResponse struct {
	JSONRPCResponse
	Result *Task     `json:"result,omitempty"`
	Error  *A2AError `json:"error,omitempty"`
}

// CancelTaskResponse represents a response to a cancel task request
type CancelTaskResponse struct {
	JSONRPCResponse
	Result *Task     `json:"result,omitempty"`
	Error  *A2AError `json:"error,omitempty"`
}

// GetTaskHistoryResponse represents a response to a get task history request
type GetTaskHistoryResponse struct {
	JSONRPCResponse
	Result *TaskHistory `json:"result,omitempty"`
	Error  *A2AError    `json:"error,omitempty"`
}

// SetTaskPushNotificationResponse represents a response to a set task push notification request
type SetTaskPushNotificationResponse struct {
	JSONRPCResponse
	Result *PushNotificationConfig `json:"result,omitempty"`
	Error  *A2AError               `json:"error,omitempty"`
}

// GetTaskPushNotificationResponse represents a response to a get task push notification request
type GetTaskPushNotificationResponse struct {
	JSONRPCResponse
	Result *PushNotificationConfig `json:"result,omitempty"`
	Error  *A2AError               `json:"error,omitempty"`
}
