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
	agentCard   models.AgentCard
	handler     TaskHandler
	port        int
	basePath    string
	taskStore   map[string]*models.Task
	taskHistory map[string][]*models.Message
	mu          sync.RWMutex
}

func NewA2AServer(agentCard models.AgentCard, handler func(*models.Task, *models.Message) (*models.Task, error)) *A2AServer {
	return &A2AServer{
		agentCard:   agentCard,
		handler:     handler,
		taskStore:   make(map[string]*models.Task),
		taskHistory: make(map[string][]*models.Message),
	}
}

// Start starts the A2A server
func (s *A2AServer) Start() error {
	mux := http.NewServeMux()
	mux.Handle(s.basePath, s)
	return http.ListenAndServe(fmt.Sprintf(":%d", s.port), mux)
}

// ServeHTTP implements the http.Handler interface
func (s *A2AServer) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req models.JSONRPCRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		// Return JSON-RPC error response with ErrorCodeInvalidRequest
		response := models.JSONRPCResponse{
			JSONRPCMessage: models.JSONRPCMessage{
				JSONRPC: "2.0",
			},
			Error: &models.JSONRPCError{
				Code:    int(models.ErrorCodeInvalidRequest),
				Message: "Invalid JSON: " + err.Error(),
			},
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(response)
		return
	}

	switch req.Method {
	case "tasks/send":
		var params models.TaskSendParams
		paramsBytes, err := json.Marshal(req.Params)
		if err != nil {
			s.sendError(w, req.ID.(string), models.ErrorCodeInvalidRequest, "Invalid parameters")
			return
		}
		if err := json.Unmarshal(paramsBytes, &params); err != nil {
			s.sendError(w, req.ID.(string), models.ErrorCodeInvalidRequest, "Invalid parameters")
			return
		}

		// Check if client wants streaming response
		if r.Header.Get("Accept") == "text/event-stream" {
			s.handleStreamingTask(w, r, params)
			return
		}

		s.handleTaskSend(w, &req, req.ID.(string))
	case "tasks/get":
		s.handleTaskGet(w, &req, req.ID.(string))
	case "tasks/cancel":
		s.handleTaskCancel(w, &req, req.ID.(string))
	default:
		s.sendError(w, req.ID.(string), models.ErrorCodeMethodNotFound, "Method not found")
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

func (s *A2AServer) handleStreamingTask(w http.ResponseWriter, r *http.Request, params models.TaskSendParams) {
	// Set headers for SSE
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	// Check if response writer supports flushing
	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "Streaming not supported", http.StatusInternalServerError)
		return
	}

	// Create a channel to receive task updates
	updates := make(chan interface{})

	// Create a done channel to signal when the goroutine is finished
	done := make(chan struct{})

	// Start task processing in a goroutine
	go func() {
		defer func() {
			close(updates) // Close updates channel when goroutine exits
			close(done)    // Signal that goroutine is done
		}()

		// Recover from any panics to ensure channels are closed
		defer func() {
			if r := recover(); r != nil {
				// Log the panic (you might want to use a proper logger)
				fmt.Printf("Recovered from panic in streaming task: %v\n", r)
			}
		}()

		s.mu.Lock()
		// Create new task
		task := &models.Task{
			ID: params.ID,
			Status: models.TaskStatus{
				State: models.TaskStateWorking,
			},
		}
		s.taskStore[task.ID] = task
		s.taskHistory[task.ID] = append(s.taskHistory[task.ID], &params.Message)
		s.mu.Unlock()

		// Send initial status update
		updates <- models.TaskStatusUpdateEvent{
			ID:     task.ID,
			Status: task.Status,
			Final:  boolPtr(false),
		}

		// Process task using the handler field
		updatedTask, err := s.handler(task, &params.Message)
		if err != nil {
			// Send error status update
			updates <- models.TaskStatusUpdateEvent{
				ID: task.ID,
				Status: models.TaskStatus{
					State: models.TaskStateFailed,
				},
				Final: boolPtr(true),
			}
			return
		}

		// Update task in store
		s.mu.Lock()
		s.taskStore[task.ID] = updatedTask
		s.mu.Unlock()

		// Send final status update
		updates <- models.TaskStatusUpdateEvent{
			ID:     updatedTask.ID,
			Status: updatedTask.Status,
			Final:  boolPtr(true),
		}
	}()

	// Stream updates to the client
	encoder := json.NewEncoder(w)
	for {
		select {
		case update, ok := <-updates:
			if !ok {
				// Channel closed, we're done
				return
			}
			resp := models.SendTaskStreamingResponse{
				Result: update,
				Error:  nil,
			}

			if err := encoder.Encode(resp); err != nil {
				return
			}
			flusher.Flush()
		case <-r.Context().Done():
			// Client disconnected
			return
		case <-done:
			// Goroutine finished
			return
		}
	}
}
