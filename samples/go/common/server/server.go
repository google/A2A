package server

import (
	"encoding/json"
	"net/http"

	"github.com/gorilla/mux"
)

// AgentServer provides the base implementation for A2A protocol servers
type AgentServer struct {
	router *mux.Router
	card   AgentCard
}

// Router returns the router for custom route handling
func (s *AgentServer) Router() *mux.Router {
	return s.router
}

// AgentCard represents the agent's metadata and capabilities
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

// NewAgentServer creates a new base agent server with the given card
func NewAgentServer(card AgentCard) *AgentServer {
	s := &AgentServer{
		router: mux.NewRouter(),
		card:   card,
	}

	s.router.HandleFunc("/agent-card", s.handleAgentCard).Methods("GET")
	return s
}

// ServeHTTP implements http.Handler
func (s *AgentServer) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	s.router.ServeHTTP(w, r)
}

func (s *AgentServer) handleAgentCard(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(s.card)
}