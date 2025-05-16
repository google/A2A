package models

// JSONRPCMessageIdentifier represents the base interface for identifying JSON-RPC messages
type JSONRPCMessageIdentifier struct {
	// ID is the request identifier. Can be a string, number, or null.
	// Responses must have the same ID as the request they relate to.
	// Notifications (requests without an expected response) should omit the ID or use null.
	ID interface{} `json:"id,omitempty"`
}

// JSONRPCMessage represents the base interface for all JSON-RPC messages
type JSONRPCMessage struct {
	JSONRPCMessageIdentifier
	// JSONRPC specifies the JSON-RPC version. Must be "2.0"
	JSONRPC string `json:"jsonrpc,omitempty"`
}

// JSONRPCRequest represents a JSON-RPC request object base structure
type JSONRPCRequest struct {
	JSONRPCMessage
	// Method is the name of the method to be invoked
	Method string `json:"method"`
	// Params are the parameters for the method
	Params interface{} `json:"params,omitempty"`
}

// JSONRPCError represents a JSON-RPC error object
type JSONRPCError struct {
	// Code is a number indicating the error type that occurred
	Code int `json:"code"`
	// Message is a string providing a short description of the error
	Message string `json:"message"`
	// Data is optional additional data about the error
	Data interface{} `json:"data,omitempty"`
}

// JSONRPCResponse represents a JSON-RPC response object
type JSONRPCResponse struct {
	JSONRPCMessage
	// Result is the result of the method invocation. Required on success.
	// Should be null or omitted if an error occurred.
	Result interface{} `json:"result,omitempty"`
	// Error is an error object if an error occurred during the request.
	// Required on failure. Should be null or omitted if the request was successful.
	Error *JSONRPCError `json:"error,omitempty"`
}
