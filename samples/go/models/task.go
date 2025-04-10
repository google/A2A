package models

// FileContentBase represents the base structure for file content
type FileContentBase struct {
	// Name is the optional name of the file
	Name *string `json:"name,omitempty"`
	// MimeType is the optional MIME type of the file content
	MimeType *string `json:"mimeType,omitempty"`
}

// FileContentBytes represents file content as base64-encoded bytes
type FileContentBytes struct {
	FileContentBase
	// Bytes is the file content encoded as a Base64 string
	Bytes string `json:"bytes"`
}

// FileContentURI represents file content as a URI
type FileContentURI struct {
	FileContentBase
	// URI is the URI pointing to the file content
	URI string `json:"uri"`
}

// FileContent represents either bytes or URI-based file content
type FileContent interface {
	IsFileContent()
}

func (FileContentBytes) IsFileContent() {}
func (FileContentURI) IsFileContent()   {}

// Part represents a part of a message or artifact
type Part struct {
	// Type identifies the type of this part
	Type *string `json:"type,omitempty"`
	// Text is the text content for text parts
	Text *string `json:"text,omitempty"`
	// File is the file content for file parts
	File FileContent `json:"file,omitempty"`
	// Data is the structured data content for data parts
	Data map[string]interface{} `json:"data,omitempty"`
	// Metadata is optional metadata associated with this part
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// Artifact represents an output or intermediate file from a task
type Artifact struct {
	// Name is an optional name for the artifact
	Name *string `json:"name,omitempty"`
	// Description is an optional description of the artifact
	Description *string `json:"description,omitempty"`
	// Parts are the constituent parts of the artifact
	Parts []Part `json:"parts"`
	// Index is an optional index for ordering artifacts
	Index *int `json:"index,omitempty"`
	// Append indicates if this artifact content should append to previous content
	Append *bool `json:"append,omitempty"`
	// Metadata is optional metadata associated with the artifact
	Metadata map[string]interface{} `json:"metadata,omitempty"`
	// LastChunk indicates if this is the last chunk of data for this artifact
	LastChunk *bool `json:"lastChunk,omitempty"`
}

// TaskStatus represents the status of a task
type TaskStatus struct {
	State TaskState `json:"state"`
}

// Task represents an A2A task
type Task struct {
	ID     string     `json:"id"`
	Status TaskStatus `json:"status"`
}

// Message represents a message in the A2A protocol
type Message struct {
	Role  string `json:"role"`
	Parts []Part `json:"parts"`
}

// TaskHistory represents the history of a task
type TaskHistory struct {
	// MessageHistory is the list of messages in chronological order
	MessageHistory []Message `json:"messageHistory,omitempty"`
}

// TaskStatusUpdateEvent represents an event for task status updates
type TaskStatusUpdateEvent struct {
	// ID is the ID of the task being updated
	ID string `json:"id"`
	// Status is the new status of the task
	Status TaskStatus `json:"status"`
	// Final indicates if this is the final update for the task
	Final *bool `json:"final,omitempty"`
	// Metadata is optional metadata associated with this update event
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// TaskArtifactUpdateEvent represents an event for task artifact updates
type TaskArtifactUpdateEvent struct {
	// ID is the ID of the task being updated
	ID string `json:"id"`
	// Artifact is the new or updated artifact for the task
	Artifact Artifact `json:"artifact"`
	// Final indicates if this is the final update for the task
	Final *bool `json:"final,omitempty"`
	// Metadata is optional metadata associated with this update event
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}
