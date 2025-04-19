package client

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
)

// Client provides methods for interacting with A2A agents
type Client struct {
	baseURL    string
	httpClient *http.Client
}

// NewClient creates a new A2A client
func NewClient(baseURL string) *Client {
	return &Client{
		baseURL:    baseURL,
		httpClient: &http.Client{},
	}
}

// GetAgentCard retrieves the agent's metadata and capabilities
func (c *Client) GetAgentCard() (*AgentCard, error) {
	resp, err := c.httpClient.Get(c.baseURL + "/agent-card")
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var card AgentCard
	if err := json.NewDecoder(resp.Body).Decode(&card); err != nil {
		return nil, err
	}

	return &card, nil
}

// SendMessage sends a message to the agent and returns a response reader
func (c *Client) SendMessage(taskID string, message Message) (*TaskResponseReader, error) {
	req := JSONRPCRequest{
		JSONRPC: "2.0",
		Method:  "tasks/sendSubscribe",
		ID:      taskID,
		Params: map[string]interface{}{
			"id":      taskID,
			"message": message,
		},
	}

	reqBody, err := json.Marshal(req)
	if err != nil {
		return nil, err
	}

	resp, err := c.httpClient.Post(c.baseURL, "application/json", bytes.NewBuffer(reqBody))
	if err != nil {
		return nil, err
	}

	return &TaskResponseReader{response: resp}, nil
}

// TaskResponseReader handles reading SSE responses from the agent
type TaskResponseReader struct {
	response *http.Response
}

// Read returns the next response from the agent, or error if the stream is closed
func (r *TaskResponseReader) Read() (*TaskResponse, error) {
	if r.response == nil {
		return nil, fmt.Errorf("response stream closed")
	}

	// Read the SSE data line
	buf := make([]byte, 1024)
	n, err := r.response.Body.Read(buf)
	if err != nil {
		r.response.Body.Close()
		r.response = nil
		return nil, err
	}

	data := string(buf[:n])
	if !isSSEData(data) {
		return nil, nil // Not a data line, skip
	}

	// Parse the JSON response
	var resp TaskResponse
	if err := json.Unmarshal([]byte(getSSEData(data)), &resp); err != nil {
		return nil, err
	}

	return &resp, nil
}

// Close closes the response stream
func (r *TaskResponseReader) Close() error {
	if r.response != nil {
		err := r.response.Body.Close()
		r.response = nil
		return err
	}
	return nil
}

// Helper types for JSON-RPC requests/responses
type JSONRPCRequest struct {
	JSONRPC string      `json:"jsonrpc"`
	Method  string      `json:"method"`
	ID      string      `json:"id"`
	Params  interface{} `json:"params"`
}

type Message struct {
	Role  string     `json:"role"`
	Parts []TextPart `json:"parts"`
}

type TextPart struct {
	Type string `json:"type"`
	Text string `json:"text"`
}

type TaskResponse struct {
	Result struct {
		ID     string     `json:"id"`
		Status TaskStatus `json:"status"`
		Final  bool       `json:"final"`
	} `json:"result"`
}

type TaskStatus struct {
	State   string   `json:"state"`
	Message *Message `json:"message,omitempty"`
}

type AgentCard struct {
	Name        string   `json:"name"`
	Description string   `json:"description"`
	Version     string   `json:"version"`
	Provider    Provider `json:"provider"`
	Capabilities struct {
		Streaming             bool `json:"streaming"`
		PushNotifications     bool `json:"pushNotifications"`
		StateTransitionHistory bool `json:"stateTransitionHistory"`
	} `json:"capabilities"`
	Authentication     interface{} `json:"authentication"`
	DefaultInputModes  []string    `json:"defaultInputModes"`
	DefaultOutputModes []string    `json:"defaultOutputModes"`
}

type Provider struct {
	Organization string `json:"organization"`
}

// Helper functions for SSE parsing
func isSSEData(line string) bool {
	return len(line) > 5 && line[:5] == "data:"
}

func getSSEData(line string) string {
	return line[5:] // Strip "data:" prefix
}