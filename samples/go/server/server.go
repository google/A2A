package server

import (
	"encoding/json"
	"fmt"
	"net/http"
	"sync"

	"a2a/models"
)

// TaskHandler is a function type that handles task processing
type TaskHandler func(task *models.Task, message *models.Message) (*models.Task, error)

// A2AServer represents an A2A server instance
type A2AServer struct {
	handler     TaskHandler
	port        int
	basePath    string
	taskStore   map[string]*models.Task
	taskHistory map[string][]*models.Message
	mu          sync.RWMutex
}

// NewA2AServer creates a new A2A server instance
func NewA2AServer(handler TaskHandler, port int, basePath string) *A2AServer {
	return &A2AServer{
		handler:     handler,
		port:        port,
		basePath:    basePath,
		taskStore:   make(map[string]*models.Task),
		taskHistory: make(map[string][]*models.Message),
	}
}

// Start starts the A2A server
func (s *A2AServer) Start() error {
	mux := http.NewServeMux()
	mux.HandleFunc(s.basePath, s.handleRequest)
	return http.ListenAndServe(fmt.Sprintf(":%d", s.port), mux)
}

// handleRequest handles incoming HTTP requests
func (s *A2AServer) handleRequest(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var request models.JSONRPCRequest
	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		s.sendError(w, "", models.ErrorCodeInvalidRequest, "Invalid request format")
		return
	}

	// Convert ID to string if it's not nil
	var idStr string
	if request.ID != nil {
		if id, ok := request.ID.(string); ok {
			idStr = id
		} else {
			s.sendError(w, "", models.ErrorCodeInvalidRequest, "Invalid request ID format")
			return
		}
	}

	switch request.Method {
	case "tasks/send":
		s.handleTaskSend(w, &request, idStr)
	case "tasks/get":
		s.handleTaskGet(w, &request, idStr)
	case "tasks/cancel":
		s.handleTaskCancel(w, &request, idStr)
	default:
		s.sendError(w, idStr, models.ErrorCodeInvalidRequest, "Unknown method")
	}
}

// handleTaskSend handles the tasks/send method
func (s *A2AServer) handleTaskSend(w http.ResponseWriter, req *models.JSONRPCRequest, id string) {
	var params models.TaskSendParams
	paramsBytes, err := json.Marshal(req.Params)
	if err != nil {
		s.sendError(w, id, models.ErrorCodeInvalidRequest, "Invalid parameters")
		return
	}
	if err := json.Unmarshal(paramsBytes, &params); err != nil {
		s.sendError(w, id, models.ErrorCodeInvalidRequest, "Invalid parameters")
		return
	}

	s.mu.Lock()
	defer s.mu.Unlock()

	// Create new task
	task := &models.Task{
		ID: params.ID,
		Status: models.TaskStatus{
			State: models.TaskStateWorking,
		},
	}

	// Process task
	updatedTask, err := s.handler(task, &params.Message)
	if err != nil {
		s.sendError(w, id, models.ErrorCodeInternalError, err.Error())
		return
	}

	// Store task and history
	s.taskStore[task.ID] = updatedTask
	s.taskHistory[task.ID] = append(s.taskHistory[task.ID], &params.Message)

	// Send response
	s.sendResponse(w, id, updatedTask)
}

// handleTaskGet handles the tasks/get method
func (s *A2AServer) handleTaskGet(w http.ResponseWriter, req *models.JSONRPCRequest, id string) {
	var params models.TaskQueryParams
	paramsBytes, err := json.Marshal(req.Params)
	if err != nil {
		s.sendError(w, id, models.ErrorCodeInvalidRequest, "Invalid parameters")
		return
	}
	if err := json.Unmarshal(paramsBytes, &params); err != nil {
		s.sendError(w, id, models.ErrorCodeInvalidRequest, "Invalid parameters")
		return
	}

	s.mu.RLock()
	defer s.mu.RUnlock()

	task, exists := s.taskStore[params.ID]
	if !exists {
		s.sendError(w, id, models.ErrorCodeTaskNotFound, "Task not found")
		return
	}

	s.sendResponse(w, id, task)
}

// handleTaskCancel handles the tasks/cancel method
func (s *A2AServer) handleTaskCancel(w http.ResponseWriter, req *models.JSONRPCRequest, id string) {
	var params models.TaskIDParams
	paramsBytes, err := json.Marshal(req.Params)
	if err != nil {
		s.sendError(w, id, models.ErrorCodeInvalidRequest, "Invalid parameters")
		return
	}
	if err := json.Unmarshal(paramsBytes, &params); err != nil {
		s.sendError(w, id, models.ErrorCodeInvalidRequest, "Invalid parameters")
		return
	}

	s.mu.Lock()
	defer s.mu.Unlock()

	task, exists := s.taskStore[params.ID]
	if !exists {
		s.sendError(w, id, models.ErrorCodeTaskNotFound, "Task not found")
		return
	}

	// Update task status to canceled
	task.Status.State = models.TaskStateCanceled
	s.taskStore[params.ID] = task

	s.sendResponse(w, id, task)
}

// sendResponse sends a JSON-RPC response
func (s *A2AServer) sendResponse(w http.ResponseWriter, id string, result interface{}) {
	response := models.JSONRPCResponse{
		JSONRPCMessage: models.JSONRPCMessage{
			JSONRPC: "2.0",
			JSONRPCMessageIdentifier: models.JSONRPCMessageIdentifier{
				ID: id,
			},
		},
		Result: result,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// sendError sends a JSON-RPC error response
func (s *A2AServer) sendError(w http.ResponseWriter, id string, code models.ErrorCode, message string) {
	response := models.JSONRPCResponse{
		JSONRPCMessage: models.JSONRPCMessage{
			JSONRPC: "2.0",
			JSONRPCMessageIdentifier: models.JSONRPCMessageIdentifier{
				ID: id,
			},
		},
		Error: &models.JSONRPCError{
			Code:    int(code),
			Message: message,
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}
