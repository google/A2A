package server

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"a2a/models"
)

// mockTaskHandler is a simple task handler for testing
func mockTaskHandler(task *models.Task, message *models.Message) (*models.Task, error) {
	task.Status.State = models.TaskStateCompleted
	return task, nil
}

func TestA2AServer_HandleTaskSend(t *testing.T) {
	server := NewA2AServer(mockTaskHandler, 8080, "/")

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

	server.handleRequest(w, req)

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
	server := NewA2AServer(mockTaskHandler, 8080, "/")

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

	server.handleRequest(w, req)

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

	server.handleRequest(w, req)

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
	server := NewA2AServer(mockTaskHandler, 8080, "/")

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

	server.handleRequest(w, req)

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

	server.handleRequest(w, req)

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
	server := NewA2AServer(mockTaskHandler, 8080, "/")

	params := models.TaskQueryParams{
		TaskIDParams: models.TaskIDParams{
			ID: "non-existent-task",
		},
	}

	reqBody, _ := json.Marshal(models.JSONRPCRequest{
		JSONRPCMessage: models.JSONRPCMessage{
			JSONRPC: "2.0",
			JSONRPCMessageIdentifier: models.JSONRPCMessageIdentifier{
				ID: "1",
			},
		},
		Method: "tasks/get",
		Params: params,
	})

	req := httptest.NewRequest("POST", "/", bytes.NewBuffer(reqBody))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	server.handleRequest(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
	}

	var response models.JSONRPCResponse
	if err := json.NewDecoder(w.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if response.Error == nil {
		t.Fatal("Expected error, got nil")
	}

	expectedCode := int(models.ErrorCodeTaskNotFound)
	if response.Error.Code != expectedCode {
		t.Errorf("Expected error code %d, got %d", expectedCode, response.Error.Code)
	}

	expectedMessage := "Task not found"
	if response.Error.Message != expectedMessage {
		t.Errorf("Expected error message %q, got %q", expectedMessage, response.Error.Message)
	}
}

// Helper function to create string pointers
func stringPtr(s string) *string {
	return &s
}
