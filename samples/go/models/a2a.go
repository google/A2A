package models

// TaskState represents the state of a task within the A2A protocol
type TaskState string

const (
	TaskStateSubmitted     TaskState = "submitted"
	TaskStateWorking       TaskState = "working"
	TaskStateInputRequired TaskState = "input-required"
	TaskStateCompleted     TaskState = "completed"
	TaskStateCanceled      TaskState = "canceled"
	TaskStateFailed        TaskState = "failed"
	TaskStateUnknown       TaskState = "unknown"
)

// AgentAuthentication defines the authentication schemes and credentials for an agent
type AgentAuthentication struct {
	// Schemes is a list of supported authentication schemes
	Schemes []string `json:"schemes"`
	// Credentials for authentication. Can be a string (e.g., token) or null if not required initially
	Credentials *string `json:"credentials,omitempty"`
}

// AgentCapabilities describes the capabilities of an agent
type AgentCapabilities struct {
	// Streaming indicates if the agent supports streaming responses
	Streaming *bool `json:"streaming,omitempty"`
	// PushNotifications indicates if the agent supports push notification mechanisms
	PushNotifications *bool `json:"pushNotifications,omitempty"`
	// StateTransitionHistory indicates if the agent supports providing state transition history
	StateTransitionHistory *bool `json:"stateTransitionHistory,omitempty"`
}

// AgentProvider represents the provider or organization behind an agent
type AgentProvider struct {
	// Organization is the name of the organization providing the agent
	Organization string `json:"organization"`
	// URL associated with the agent provider
	URL *string `json:"url,omitempty"`
}

// AgentSkill defines a specific skill or capability offered by an agent
type AgentSkill struct {
	// ID is the unique identifier for the skill
	ID string `json:"id"`
	// Name is the human-readable name of the skill
	Name string `json:"name"`
	// Description is an optional description of the skill
	Description *string `json:"description,omitempty"`
	// Tags is an optional list of tags associated with the skill for categorization
	Tags []string `json:"tags,omitempty"`
	// Examples is an optional list of example inputs or use cases for the skill
	Examples []string `json:"examples,omitempty"`
	// InputModes is an optional list of input modes supported by this skill
	InputModes []string `json:"inputModes,omitempty"`
	// OutputModes is an optional list of output modes supported by this skill
	OutputModes []string `json:"outputModes,omitempty"`
}

// AgentCard represents the metadata card for an agent
type AgentCard struct {
	// Name is the name of the agent
	Name string `json:"name"`
	// Description is an optional description of the agent
	Description *string `json:"description,omitempty"`
	// URL is the base URL endpoint for interacting with the agent
	URL string `json:"url"`
	// Provider is information about the provider of the agent
	Provider *AgentProvider `json:"provider,omitempty"`
	// Version is the version identifier for the agent or its API
	Version string `json:"version"`
	// DocumentationURL is an optional URL pointing to the agent's documentation
	DocumentationURL *string `json:"documentationUrl,omitempty"`
	// Capabilities are the capabilities supported by the agent
	Capabilities AgentCapabilities `json:"capabilities"`
	// Authentication details required to interact with the agent
	Authentication *AgentAuthentication `json:"authentication,omitempty"`
	// DefaultInputModes are the default input modes supported by the agent
	DefaultInputModes []string `json:"defaultInputModes,omitempty"`
	// DefaultOutputModes are the default output modes supported by the agent
	DefaultOutputModes []string `json:"defaultOutputModes,omitempty"`
	// Skills is the list of specific skills offered by the agent
	Skills []AgentSkill `json:"skills"`
}
