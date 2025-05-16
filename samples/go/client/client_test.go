package client

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"a2a/models"
)

func TestSendTask(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var req models.JSONRPCRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			t.Fatal(err)
		}

		if req.Method != "tasks/send" {
			t.Errorf("expected method tasks/send, got %s", req.Method)
		}

		task := &models.Task{
			ID: "123",
			Status: models.TaskStatus{
				State: models.TaskStateSubmitted,
			},
		}

		resp := models.JSONRPCResponse{
			JSONRPCMessage: models.JSONRPCMessage{
				JSONRPC: "2.0",
			},
			Result: task,
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resp)
	}))
	defer server.Close()

	client := NewClient(server.URL)
	params := models.TaskSendParams{
		ID: "123",
		Message: models.Message{
			Role: "user",
			Parts: []models.Part{
				{
					Text: stringPtr("test message"),
				},
			},
		},
	}

	resp, err := client.SendTask(params)
	if err != nil {
		t.Fatal(err)
	}

	task, ok := resp.Result.(*models.Task)
	if !ok {
		t.Fatal("expected result to be a Task")
	}

	if task.ID != "123" {
		t.Errorf("expected task ID 123, got %s", task.ID)
	}

	if task.Status.State != models.TaskStateSubmitted {
		t.Errorf("expected task status %s, got %s", models.TaskStateSubmitted, task.Status.State)
	}
}

func TestGetTask(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var req models.JSONRPCRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			t.Fatal(err)
		}

		if req.Method != "tasks/get" {
			t.Errorf("expected method tasks/get, got %s", req.Method)
		}

		task := &models.Task{
			ID: "123",
			Status: models.TaskStatus{
				State: models.TaskStateCompleted,
			},
		}

		resp := models.JSONRPCResponse{
			JSONRPCMessage: models.JSONRPCMessage{
				JSONRPC: "2.0",
			},
			Result: task,
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resp)
	}))
	defer server.Close()

	client := NewClient(server.URL)
	params := models.TaskQueryParams{
		TaskIDParams: models.TaskIDParams{
			ID: "123",
		},
	}

	resp, err := client.GetTask(params)
	if err != nil {
		t.Fatal(err)
	}

	task, ok := resp.Result.(*models.Task)
	if !ok {
		t.Fatal("expected result to be a Task")
	}

	if task.ID != "123" {
		t.Errorf("expected task ID 123, got %s", task.ID)
	}

	if task.Status.State != models.TaskStateCompleted {
		t.Errorf("expected task status %s, got %s", models.TaskStateCompleted, task.Status.State)
	}
}

func TestCancelTask(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var req models.JSONRPCRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			t.Fatal(err)
		}

		if req.Method != "tasks/cancel" {
			t.Errorf("expected method tasks/cancel, got %s", req.Method)
		}

		task := &models.Task{
			ID: "123",
			Status: models.TaskStatus{
				State: models.TaskStateCanceled,
			},
		}

		resp := models.JSONRPCResponse{
			JSONRPCMessage: models.JSONRPCMessage{
				JSONRPC: "2.0",
			},
			Result: task,
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resp)
	}))
	defer server.Close()

	client := NewClient(server.URL)
	params := models.TaskIDParams{
		ID: "123",
	}

	resp, err := client.CancelTask(params)
	if err != nil {
		t.Fatal(err)
	}

	task, ok := resp.Result.(*models.Task)
	if !ok {
		t.Fatal("expected result to be a Task")
	}

	if task.ID != "123" {
		t.Errorf("expected task ID 123, got %s", task.ID)
	}

	if task.Status.State != models.TaskStateCanceled {
		t.Errorf("expected task status %s, got %s", models.TaskStateCanceled, task.Status.State)
	}
}

func TestErrorResponse(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		resp := models.JSONRPCResponse{
			JSONRPCMessage: models.JSONRPCMessage{
				JSONRPC: "2.0",
			},
			Error: &models.JSONRPCError{
				Code:    -32000,
				Message: "Task not found",
			},
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resp)
	}))
	defer server.Close()

	client := NewClient(server.URL)
	params := models.TaskQueryParams{
		TaskIDParams: models.TaskIDParams{
			ID: "123",
		},
	}

	_, err := client.GetTask(params)
	if err == nil {
		t.Fatal("expected error, got nil")
	}

	expectedError := "A2A error: Task not found (code: -32000)"
	if err.Error() != expectedError {
		t.Errorf("expected error %q, got %q", expectedError, err.Error())
	}
}

func stringPtr(s string) *string {
	return &s
}
