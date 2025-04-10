package client

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"a2a/models"
)

// Client represents an A2A protocol client
type Client struct {
	baseURL    string
	httpClient *http.Client
}

// NewClient creates a new A2A client
func NewClient(baseURL string) *Client {
	return &Client{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// SendTask sends a task message to the agent
func (c *Client) SendTask(params models.TaskSendParams) (*models.JSONRPCResponse, error) {
	req := models.JSONRPCRequest{
		JSONRPCMessage: models.JSONRPCMessage{
			JSONRPC: "2.0",
		},
		Method: "tasks/send",
		Params: params,
	}

	var resp models.JSONRPCResponse
	if err := c.doRequest(req, &resp); err != nil {
		return nil, err
	}

	if resp.Error != nil {
		return nil, fmt.Errorf("A2A error: %s (code: %d)", resp.Error.Message, resp.Error.Code)
	}

	return &resp, nil
}

// GetTask retrieves the status of a task
func (c *Client) GetTask(params models.TaskQueryParams) (*models.JSONRPCResponse, error) {
	req := models.JSONRPCRequest{
		JSONRPCMessage: models.JSONRPCMessage{
			JSONRPC: "2.0",
		},
		Method: "tasks/get",
		Params: params,
	}

	var resp models.JSONRPCResponse
	if err := c.doRequest(req, &resp); err != nil {
		return nil, err
	}

	if resp.Error != nil {
		return nil, fmt.Errorf("A2A error: %s (code: %d)", resp.Error.Message, resp.Error.Code)
	}

	return &resp, nil
}

// CancelTask cancels a task
func (c *Client) CancelTask(params models.TaskIDParams) (*models.JSONRPCResponse, error) {
	req := models.JSONRPCRequest{
		JSONRPCMessage: models.JSONRPCMessage{
			JSONRPC: "2.0",
		},
		Method: "tasks/cancel",
		Params: params,
	}

	var resp models.JSONRPCResponse
	if err := c.doRequest(req, &resp); err != nil {
		return nil, err
	}

	if resp.Error != nil {
		return nil, fmt.Errorf("A2A error: %s (code: %d)", resp.Error.Message, resp.Error.Code)
	}

	return &resp, nil
}

// doRequest performs the HTTP request and handles the response
func (c *Client) doRequest(req interface{}, resp *models.JSONRPCResponse) error {
	body, err := json.Marshal(req)
	if err != nil {
		return fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", c.baseURL, bytes.NewBuffer(body))
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")

	httpResp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return fmt.Errorf("failed to send request: %w", err)
	}
	defer httpResp.Body.Close()

	if httpResp.StatusCode != http.StatusOK {
		return fmt.Errorf("unexpected status code: %d", httpResp.StatusCode)
	}

	// First decode into a map to handle the Result field correctly
	var rawResp struct {
		JSONRPC string               `json:"jsonrpc"`
		ID      interface{}          `json:"id,omitempty"`
		Result  json.RawMessage      `json:"result,omitempty"`
		Error   *models.JSONRPCError `json:"error,omitempty"`
	}

	if err := json.NewDecoder(httpResp.Body).Decode(&rawResp); err != nil {
		return fmt.Errorf("failed to decode response: %w", err)
	}

	// Copy the basic fields
	resp.JSONRPCMessage.JSONRPC = rawResp.JSONRPC
	resp.JSONRPCMessage.JSONRPCMessageIdentifier.ID = rawResp.ID
	resp.Error = rawResp.Error

	// If there's a result, try to decode it as a Task
	if len(rawResp.Result) > 0 {
		var task models.Task
		if err := json.Unmarshal(rawResp.Result, &task); err != nil {
			return fmt.Errorf("failed to decode task: %w", err)
		}
		resp.Result = &task
	}

	return nil
}
