package server

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"a2a/models"
)

// mockTaskHandler is a simple task handler for testing
func mockTaskHandler(task *models.Task, message *models.Message) (*models.Task, error) {
	task.Status.State = models.TaskStateCompleted
	return task, nil
}

// mockErrorTaskHandler is a task handler that returns an error for testing
func mockErrorTaskHandler(task *models.Task, message *models.Message) (*models.Task, error) {
	return nil, fmt.Errorf("test error")
}

// mockAgentCard is a simple agent card for testing
var mockAgentCard = models.AgentCard{
	Name:        "Test Agent",
	Description: stringPtr("A test agent for unit tests"),
	URL:         "http://localhost:8080",
	Version:     "1.0.0",
	Capabilities: models.AgentCapabilities{
		Streaming:              boolPtr(true),
		PushNotifications:      boolPtr(false),
		StateTransitionHistory: boolPtr(true),
	},
	Skills: []models.AgentSkill{
		{
			ID:          "test-skill",
			Name:        "Test Skill",
			Description: stringPtr("A test skill for unit tests"),
		},
	},
}

// mockNonFlushingResponseWriter is a response writer that doesn't implement http.Flusher
type mockNonFlushingResponseWriter struct {
	header     http.Header
	body       bytes.Buffer
	statusCode int
}

func (w *mockNonFlushingResponseWriter) Header() http.Header {
	return w.header
}

func (w *mockNonFlushingResponseWriter) Write(data []byte) (int, error) {
	return w.body.Write(data)
}

func (w *mockNonFlushingResponseWriter) WriteHeader(statusCode int) {
	w.statusCode = statusCode
}

func TestA2AServer_HandleTaskSend(t *testing.T) {
	server := NewA2AServer(mockAgentCard, mockTaskHandler)
	server.port = 8080
	server.basePath = "/"

	// Create a test request
	params := models.TaskSendParams{
		ID: "test-task-1",
		Message: models.Message{
			Role: "user",
			Parts: []models.Part{
				{Text: stringPtr("Hello")},
			},
		},
	}

	reqBody, _ := json.Marshal(models.JSONRPCRequest{
		JSONRPCMessage: models.JSONRPCMessage{
			JSONRPC: "2.0",
			JSONRPCMessageIdentifier: models.JSONRPCMessageIdentifier{
				ID: "1",
			},
		},
		Method: "tasks/send",
		Params: params,
	})

	req := httptest.NewRequest("POST", "/", bytes.NewBuffer(reqBody))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	server.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
	}

	var response models.JSONRPCResponse
	if err := json.NewDecoder(w.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if response.Error != nil {
		t.Errorf("Expected no error, got %v", response.Error)
	}

	// Unmarshal the result into a Task
	resultBytes, err := json.Marshal(response.Result)
	if err != nil {
		t.Fatalf("Failed to marshal result: %v", err)
	}

	var task models.Task
	if err := json.Unmarshal(resultBytes, &task); err != nil {
		t.Fatalf("Failed to unmarshal task: %v", err)
	}

	if task.ID != "test-task-1" {
		t.Errorf("Expected task ID %s, got %s", "test-task-1", task.ID)
	}

	if task.Status.State != models.TaskStateCompleted {
		t.Errorf("Expected task state %s, got %s", models.TaskStateCompleted, task.Status.State)
	}
}

func TestA2AServer_HandleTaskGet(t *testing.T) {
	server := NewA2AServer(mockAgentCard, mockTaskHandler)
	server.port = 8080
	server.basePath = "/"

	// First create a task
	params := models.TaskSendParams{
		ID: "test-task-1",
		Message: models.Message{
			Role: "user",
			Parts: []models.Part{
				{Text: stringPtr("Hello")},
			},
		},
	}

	reqBody, _ := json.Marshal(models.JSONRPCRequest{
		JSONRPCMessage: models.JSONRPCMessage{
			JSONRPC: "2.0",
			JSONRPCMessageIdentifier: models.JSONRPCMessageIdentifier{
				ID: "1",
			},
		},
		Method: "tasks/send",
		Params: params,
	})

	req := httptest.NewRequest("POST", "/", bytes.NewBuffer(reqBody))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	server.ServeHTTP(w, req)

	// Now try to get the task
	getParams := models.TaskQueryParams{
		TaskIDParams: models.TaskIDParams{
			ID: "test-task-1",
		},
	}

	reqBody, _ = json.Marshal(models.JSONRPCRequest{
		JSONRPCMessage: models.JSONRPCMessage{
			JSONRPC: "2.0",
			JSONRPCMessageIdentifier: models.JSONRPCMessageIdentifier{
				ID: "2",
			},
		},
		Method: "tasks/get",
		Params: getParams,
	})

	req = httptest.NewRequest("POST", "/", bytes.NewBuffer(reqBody))
	req.Header.Set("Content-Type", "application/json")
	w = httptest.NewRecorder()

	server.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
	}

	var response models.JSONRPCResponse
	if err := json.NewDecoder(w.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if response.Error != nil {
		t.Errorf("Expected no error, got %v", response.Error)
	}

	// Unmarshal the result into a Task
	resultBytes, err := json.Marshal(response.Result)
	if err != nil {
		t.Fatalf("Failed to marshal result: %v", err)
	}

	var task models.Task
	if err := json.Unmarshal(resultBytes, &task); err != nil {
		t.Fatalf("Failed to unmarshal task: %v", err)
	}

	if task.ID != "test-task-1" {
		t.Errorf("Expected task ID %s, got %s", "test-task-1", task.ID)
	}
}

func TestA2AServer_HandleTaskCancel(t *testing.T) {
	server := NewA2AServer(mockAgentCard, mockTaskHandler)
	server.port = 8080
	server.basePath = "/"

	// First create a task
	params := models.TaskSendParams{
		ID: "test-task-1",
		Message: models.Message{
			Role: "user",
			Parts: []models.Part{
				{Text: stringPtr("Hello")},
			},
		},
	}

	reqBody, _ := json.Marshal(models.JSONRPCRequest{
		JSONRPCMessage: models.JSONRPCMessage{
			JSONRPC: "2.0",
			JSONRPCMessageIdentifier: models.JSONRPCMessageIdentifier{
				ID: "1",
			},
		},
		Method: "tasks/send",
		Params: params,
	})

	req := httptest.NewRequest("POST", "/", bytes.NewBuffer(reqBody))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	server.ServeHTTP(w, req)

	// Now try to cancel the task
	cancelParams := models.TaskIDParams{
		ID: "test-task-1",
	}

	reqBody, _ = json.Marshal(models.JSONRPCRequest{
		JSONRPCMessage: models.JSONRPCMessage{
			JSONRPC: "2.0",
			JSONRPCMessageIdentifier: models.JSONRPCMessageIdentifier{
				ID: "3",
			},
		},
		Method: "tasks/cancel",
		Params: cancelParams,
	})

	req = httptest.NewRequest("POST", "/", bytes.NewBuffer(reqBody))
	req.Header.Set("Content-Type", "application/json")
	w = httptest.NewRecorder()

	server.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
	}

	var response models.JSONRPCResponse
	if err := json.NewDecoder(w.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if response.Error != nil {
		t.Errorf("Expected no error, got %v", response.Error)
	}

	// Unmarshal the result into a Task
	resultBytes, err := json.Marshal(response.Result)
	if err != nil {
		t.Fatalf("Failed to marshal result: %v", err)
	}

	var task models.Task
	if err := json.Unmarshal(resultBytes, &task); err != nil {
		t.Fatalf("Failed to unmarshal task: %v", err)
	}

	if task.ID != "test-task-1" {
		t.Errorf("Expected task ID %s, got %s", "test-task-1", task.ID)
	}

	if task.Status.State != models.TaskStateCanceled {
		t.Errorf("Expected task state %s, got %s", models.TaskStateCanceled, task.Status.State)
	}
}

func TestErrorResponse(t *testing.T) {
	server := NewA2AServer(mockAgentCard, mockTaskHandler)
	server.port = 8080
	server.basePath = "/"

	// Test with invalid JSON
	req := httptest.NewRequest("POST", "/", bytes.NewBufferString("invalid json"))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	server.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
	}

	var response models.JSONRPCResponse
	if err := json.NewDecoder(w.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if response.Error == nil {
		t.Error("Expected error, got nil")
	}

	if response.Error.Code != int(models.ErrorCodeInvalidRequest) {
		t.Errorf("Expected error code %d, got %d", models.ErrorCodeInvalidRequest, response.Error.Code)
	}
}

func TestA2AServer_HandleStreamingTask(t *testing.T) {
	server := NewA2AServer(mockAgentCard, mockTaskHandler)
	server.port = 8080
	server.basePath = "/"

	// Create a test request
	params := models.TaskSendParams{
		ID: "test-task-1",
		Message: models.Message{
			Role: "user",
			Parts: []models.Part{
				{Text: stringPtr("Hello")},
			},
		},
	}

	reqBody, _ := json.Marshal(models.JSONRPCRequest{
		JSONRPCMessage: models.JSONRPCMessage{
			JSONRPC: "2.0",
			JSONRPCMessageIdentifier: models.JSONRPCMessageIdentifier{
				ID: "1",
			},
		},
		Method: "tasks/send",
		Params: params,
	})

	req := httptest.NewRequest("POST", "/", bytes.NewBuffer(reqBody))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "text/event-stream")
	w := httptest.NewRecorder()

	server.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
	}

	// Check that the response has the correct headers
	if w.Header().Get("Content-Type") != "text/event-stream" {
		t.Errorf("Expected Content-Type text/event-stream, got %s", w.Header().Get("Content-Type"))
	}
	if w.Header().Get("Cache-Control") != "no-cache" {
		t.Errorf("Expected Cache-Control no-cache, got %s", w.Header().Get("Cache-Control"))
	}
	if w.Header().Get("Connection") != "keep-alive" {
		t.Errorf("Expected Connection keep-alive, got %s", w.Header().Get("Connection"))
	}

	// Parse the streaming response
	// The response should contain multiple JSON objects, one per line
	responseLines := strings.Split(strings.TrimSpace(w.Body.String()), "\n")
	if len(responseLines) < 2 {
		t.Errorf("Expected at least 2 response lines, got %d", len(responseLines))
	}

	// Check the initial status update
	var initialResponse models.SendTaskStreamingResponse
	if err := json.Unmarshal([]byte(responseLines[0]), &initialResponse); err != nil {
		t.Fatalf("Failed to unmarshal initial response: %v", err)
	}

	if initialResponse.Error != nil {
		t.Errorf("Expected no error in initial response, got %v", initialResponse.Error)
	}

	// Check that the result is a TaskStatusUpdateEvent
	initialResultBytes, err := json.Marshal(initialResponse.Result)
	if err != nil {
		t.Fatalf("Failed to marshal initial result: %v", err)
	}

	var initialEvent models.TaskStatusUpdateEvent
	if err := json.Unmarshal(initialResultBytes, &initialEvent); err != nil {
		t.Fatalf("Failed to unmarshal initial event: %v", err)
	}

	if initialEvent.ID != "test-task-1" {
		t.Errorf("Expected task ID %s, got %s", "test-task-1", initialEvent.ID)
	}

	if initialEvent.Status.State != models.TaskStateWorking {
		t.Errorf("Expected task state %s, got %s", models.TaskStateWorking, initialEvent.Status.State)
	}

	if initialEvent.Final == nil || *initialEvent.Final {
		t.Error("Expected Final to be false for initial update")
	}

	// Check the final status update
	var finalResponse models.SendTaskStreamingResponse
	if err := json.Unmarshal([]byte(responseLines[len(responseLines)-1]), &finalResponse); err != nil {
		t.Fatalf("Failed to unmarshal final response: %v", err)
	}

	if finalResponse.Error != nil {
		t.Errorf("Expected no error in final response, got %v", finalResponse.Error)
	}

	// Check that the result is a TaskStatusUpdateEvent
	finalResultBytes, err := json.Marshal(finalResponse.Result)
	if err != nil {
		t.Fatalf("Failed to marshal final result: %v", err)
	}

	var finalEvent models.TaskStatusUpdateEvent
	if err := json.Unmarshal(finalResultBytes, &finalEvent); err != nil {
		t.Fatalf("Failed to unmarshal final event: %v", err)
	}

	if finalEvent.ID != "test-task-1" {
		t.Errorf("Expected task ID %s, got %s", "test-task-1", finalEvent.ID)
	}

	if finalEvent.Status.State != models.TaskStateCompleted {
		t.Errorf("Expected task state %s, got %s", models.TaskStateCompleted, finalEvent.Status.State)
	}

	if finalEvent.Final == nil || !*finalEvent.Final {
		t.Error("Expected Final to be true for final update")
	}
}

func TestA2AServer_HandleStreamingTaskError(t *testing.T) {
	server := NewA2AServer(mockAgentCard, mockErrorTaskHandler)
	server.port = 8080
	server.basePath = "/"

	// Create a test request
	params := models.TaskSendParams{
		ID: "test-task-1",
		Message: models.Message{
			Role: "user",
			Parts: []models.Part{
				{Text: stringPtr("Hello")},
			},
		},
	}

	reqBody, _ := json.Marshal(models.JSONRPCRequest{
		JSONRPCMessage: models.JSONRPCMessage{
			JSONRPC: "2.0",
			JSONRPCMessageIdentifier: models.JSONRPCMessageIdentifier{
				ID: "1",
			},
		},
		Method: "tasks/send",
		Params: params,
	})

	req := httptest.NewRequest("POST", "/", bytes.NewBuffer(reqBody))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "text/event-stream")
	w := httptest.NewRecorder()

	server.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
	}

	// Check that the response has the correct headers
	if w.Header().Get("Content-Type") != "text/event-stream" {
		t.Errorf("Expected Content-Type text/event-stream, got %s", w.Header().Get("Content-Type"))
	}

	// Parse the streaming response
	// The response should contain multiple JSON objects, one per line
	responseLines := strings.Split(strings.TrimSpace(w.Body.String()), "\n")
	if len(responseLines) < 2 {
		t.Errorf("Expected at least 2 response lines, got %d", len(responseLines))
	}

	// Check the initial status update
	var initialResponse models.SendTaskStreamingResponse
	if err := json.Unmarshal([]byte(responseLines[0]), &initialResponse); err != nil {
		t.Fatalf("Failed to unmarshal initial response: %v", err)
	}

	if initialResponse.Error != nil {
		t.Errorf("Expected no error in initial response, got %v", initialResponse.Error)
	}

	// Check that the result is a TaskStatusUpdateEvent
	initialResultBytes, err := json.Marshal(initialResponse.Result)
	if err != nil {
		t.Fatalf("Failed to marshal initial result: %v", err)
	}

	var initialEvent models.TaskStatusUpdateEvent
	if err := json.Unmarshal(initialResultBytes, &initialEvent); err != nil {
		t.Fatalf("Failed to unmarshal initial event: %v", err)
	}

	if initialEvent.ID != "test-task-1" {
		t.Errorf("Expected task ID %s, got %s", "test-task-1", initialEvent.ID)
	}

	if initialEvent.Status.State != models.TaskStateWorking {
		t.Errorf("Expected task state %s, got %s", models.TaskStateWorking, initialEvent.Status.State)
	}

	if initialEvent.Final == nil || *initialEvent.Final {
		t.Error("Expected Final to be false for initial update")
	}

	// Check the error status update
	var finalResponse models.SendTaskStreamingResponse
	if err := json.Unmarshal([]byte(responseLines[len(responseLines)-1]), &finalResponse); err != nil {
		t.Fatalf("Failed to unmarshal final response: %v", err)
	}

	if finalResponse.Error != nil {
		t.Errorf("Expected no error in final response, got %v", finalResponse.Error)
	}

	// Check that the result is a TaskStatusUpdateEvent
	finalResultBytes, err := json.Marshal(finalResponse.Result)
	if err != nil {
		t.Fatalf("Failed to marshal final result: %v", err)
	}

	var finalEvent models.TaskStatusUpdateEvent
	if err := json.Unmarshal(finalResultBytes, &finalEvent); err != nil {
		t.Fatalf("Failed to unmarshal final event: %v", err)
	}

	if finalEvent.ID != "test-task-1" {
		t.Errorf("Expected task ID %s, got %s", "test-task-1", finalEvent.ID)
	}

	if finalEvent.Status.State != models.TaskStateFailed {
		t.Errorf("Expected task state %s, got %s", models.TaskStateFailed, finalEvent.Status.State)
	}

	if finalEvent.Final == nil || !*finalEvent.Final {
		t.Error("Expected Final to be true for final update")
	}
}

func TestA2AServer_HandleStreamingTaskNoFlusher(t *testing.T) {
	server := NewA2AServer(mockAgentCard, mockTaskHandler)
	server.port = 8080
	server.basePath = "/"

	// Create a test request
	params := models.TaskSendParams{
		ID: "test-task-1",
		Message: models.Message{
			Role: "user",
			Parts: []models.Part{
				{Text: stringPtr("Hello")},
			},
		},
	}

	reqBody, _ := json.Marshal(models.JSONRPCRequest{
		JSONRPCMessage: models.JSONRPCMessage{
			JSONRPC: "2.0",
			JSONRPCMessageIdentifier: models.JSONRPCMessageIdentifier{
				ID: "1",
			},
		},
		Method: "tasks/send",
		Params: params,
	})

	req := httptest.NewRequest("POST", "/", bytes.NewBuffer(reqBody))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "text/event-stream")
	w := &mockNonFlushingResponseWriter{
		header: make(http.Header),
	}

	server.ServeHTTP(w, req)

	if w.statusCode != http.StatusInternalServerError {
		t.Errorf("Expected status code %d, got %d", http.StatusInternalServerError, w.statusCode)
	}

	if w.body.String() != "Streaming not supported\n" {
		t.Errorf("Expected error message 'Streaming not supported', got '%s'", w.body.String())
	}
}

func testStringPtr(s string) *string {
	return &s
}

func testBoolPtr(b bool) *bool {
	return &b
}
