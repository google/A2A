package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/a2a/samples/go/common/server"
	"github.com/google/generative-ai-go/genai"
	"google.golang.org/api/option"
)

type CurrencyAgent struct {
	*server.AgentServer
	llm       *genai.Client
	exchanger *ExchangeRateTool
	router    *gin.Engine
}

func NewCurrencyAgent() *CurrencyAgent {
	apiKey := os.Getenv("GOOGLE_API_KEY")
	if apiKey == "" {
		log.Fatal("GOOGLE_API_KEY environment variable is required")
	}

	card := server.AgentCard{
		Name:        "Currency Exchange Agent",
		Description: "An agent that can help with currency conversions and answer general questions about exchange rates.",
		Version:     "1.0.0",
		Provider:    server.Provider{Organization: "A2A Samples"},
	}
	card.Capabilities.Streaming = true
	card.Capabilities.StateTransitionHistory = true
	card.DefaultInputModes = []string{"text"}
	card.DefaultOutputModes = []string{"text"}

	client, err := genai.NewClient(context.Background(), option.WithAPIKey(apiKey))
	if err != nil {
		log.Fatalf("Failed to create Gemini client: %v", err)
	}

	router := gin.Default()
	agent := &CurrencyAgent{
		AgentServer: server.NewAgentServer(card),
		llm:         client,
		exchanger:   NewExchangeRateTool(),
		router:      router,
	}

	// Setup CORS
	router.Use(func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}
		c.Next()
	})

	// Define routes
	router.POST("/", agent.handleRequest)
	router.GET("/.well-known/agent.json", agent.getAgentCard)

	return agent
}

type CurrencyResponse struct {
	Amount float64            `json:"amount"`
	Base   string             `json:"base"`
	Date   string             `json:"date"`
	Rates  map[string]float64 `json:"rates"`
}

type ExchangeRateTool struct {
	client *http.Client
}

func NewExchangeRateTool() *ExchangeRateTool {
	return &ExchangeRateTool{
		client: &http.Client{Timeout: 10 * time.Second},
	}
}

func (t *ExchangeRateTool) GetExchangeRate(from, to string) (*CurrencyResponse, error) {
	from, to = strings.ToUpper(from), strings.ToUpper(to)
	url := fmt.Sprintf("https://api.frankfurter.app/latest?from=%s&to=%s", from, to)

	log.Printf("Fetching exchange rate from %s to %s...", from, to)
	resp, err := t.client.Get(url)
	if err != nil {
		return nil, fmt.Errorf("request error: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error %d: %s", resp.StatusCode, string(body))
	}

	var result CurrencyResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("decode error: %w", err)
	}

	log.Printf("Got exchange rate response: %+v", result)
	if result.Base == "" || len(result.Rates) == 0 {
		return nil, fmt.Errorf("invalid response")
	}
	return &result, nil
}

func (a *CurrencyAgent) handleRequest(c *gin.Context) {
	var request map[string]interface{}
	if err := c.BindJSON(&request); err != nil {
		c.JSON(400, Response{
			JSONRPC: "2.0",
			ID:      "",
			Error: &Error{
				Code:    -32700,
				Message: "Parse error",
			},
		})
		return
	}

	// Handle different methods
	method, ok := request["method"].(string)
	if !ok {
		c.JSON(400, Response{
			JSONRPC: "2.0",
			ID:      request["id"].(string),
			Error: &Error{
				Code:    -32600,
				Message: "Invalid Request",
			},
		})
		return
	}

	switch method {
	case "tasks/send", "tasks/sendSubscribe":
		a.handleTask(c, request)
	default:
		c.JSON(400, Response{
			JSONRPC: "2.0",
			ID:      request["id"].(string),
			Error: &Error{
				Code:    -32601,
				Message: "Method not found",
			},
		})
	}
}

func (a *CurrencyAgent) handleTask(c *gin.Context, request map[string]interface{}) {
	params, ok := request["params"].(map[string]interface{})
	if !ok {
		c.JSON(400, Response{
			JSONRPC: "2.0",
			ID:      request["id"].(string),
			Error: &Error{
				Code:    -32602,
				Message: "Invalid params",
			},
		})
		return
	}

	message, ok := params["message"].(map[string]interface{})
	if !ok {
		c.JSON(400, errorResponse(request["id"].(string), "Invalid message"))
		return
	}

	// Process the message and return appropriate response
	// For now, just echo back a simple response
	c.JSON(200, Response{
		JSONRPC: "2.0",
		ID:      request["id"].(string),
		Result: map[string]interface{}{
			"id": params["id"],
			"status": map[string]interface{}{
				"state": "completed",
				"message": map[string]interface{}{
					"role": "agent",
					"parts": []map[string]interface{}{
						{
							"type": "text",
							"text": "Echo: " + message["text"].(string),
						},
					},
				},
			},
		},
	})
}

func (a *CurrencyAgent) getAgentCard(c *gin.Context) {
	c.JSON(200, map[string]interface{}{
		"name":        "Currency Agent",
		"description": "An agent that helps with currency conversions",
		"version":     "1.0.0",
		"capabilities": map[string]interface{}{
			"streaming":             true,
			"pushNotifications":     false,
			"stateTransitionHistory": true,
		},
		"defaultInputModes":  []string{"text"},
		"defaultOutputModes": []string{"text"},
	})
}

func workingPayload(id string) map[string]interface{} {
	return map[string]interface{}{
		"jsonrpc": "2.0",
		"result": map[string]interface{}{
			"id": id,
			"status": map[string]interface{}{
				"state": "working",
				"message": map[string]interface{}{
					"role": "agent",
					"parts": []map[string]interface{}{{
						"type": "text",
						"text": "Let me help you with that...",
					}},
				},
				"timestamp": time.Now(),
			},
		},
	}
}

func completedPayload(id, txt string) map[string]interface{} {
	return map[string]interface{}{
		"jsonrpc": "2.0",
		"result": map[string]interface{}{
			"id": id,
			"status": map[string]interface{}{
				"state": "completed",
				"message": map[string]interface{}{
					"role": "agent",
					"parts": []map[string]interface{}{{
						"type": "text",
						"text": txt,
					}},
				},
				"timestamp": time.Now(),
			},
		},
		"final": true,
	}
}

func failurePayload(id, errMsg string) map[string]interface{} {
	return map[string]interface{}{
		"jsonrpc": "2.0",
		"result": map[string]interface{}{
			"id": id,
			"status": map[string]interface{}{
				"state": "failed",
				"message": map[string]interface{}{
					"role": "agent",
					"parts": []map[string]interface{}{{
						"type": "text",
						"text": errMsg,
					}},
				},
				"timestamp": time.Now(),
			},
		},
		"final": true,
	}
}

func writeSSE(w http.ResponseWriter, f http.Flusher, data interface{}) {
	b, _ := json.Marshal(data)
	fmt.Fprintf(w, "data: %s\n\n", b)
	f.Flush()
}

func main() {
	host := flag.String("host", "localhost", "Host to listen on")
	port := flag.String("port", "10000", "Port to listen on")
	flag.Parse()

	agent := NewCurrencyAgent()
	addr := fmt.Sprintf("%s:%s", *host, *port)
	log.Printf("Starting Currency Exchange Agent on http://%s", addr)
	log.Fatal(http.ListenAndServe(addr, agent))
}

// Response represents the JSON-RPC response structure
type Response struct {
	JSONRPC string       `json:"jsonrpc"`
	ID      string       `json:"id"`
	Result  interface{} `json:"result,omitempty"`
	Error   *Error      `json:"error,omitempty"`
}

// Error represents an error in the JSON-RPC response
type Error struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

func errorResponse(id, errMsg string) Response {
	return Response{
		JSONRPC: "2.0",
		ID:      id,
		Error: &Error{
			Code:    -32602,
			Message: errMsg,
		},
	}
}
