package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/google/uuid"
)

// ANSI color codes
const (
	colorReset  = "\033[0m"
	colorRed    = "\033[31m"
	colorGreen  = "\033[32m"
	colorYellow = "\033[33m"
	colorBlue   = "\033[34m"
	colorPurple = "\033[35m"
	colorCyan   = "\033[36m"
	colorGray   = "\033[90m"
)

type Message struct {
	Role  string     `json:"role"`
	Parts []TextPart `json:"parts"`
}

type TextPart struct {
	Type string `json:"type"`
	Text string `json:"text"`
}

// AgentCard represents the agent's metadata and capabilities
type AgentCard struct {
	Name        string   `json:"name"`
	Description string   `json:"description,omitempty"`
	URL         string   `json:"url"`
	Provider    Provider `json:"provider,omitempty"`
	Version     string   `json:"version"`
	Documentation string `json:"documentationUrl,omitempty"`
	Capabilities struct {
		Streaming             bool `json:"streaming"`
		PushNotifications     bool `json:"pushNotifications"`
		StateTransitionHistory bool `json:"stateTransitionHistory"`
	} `json:"capabilities"`
	Authentication     interface{} `json:"authentication,omitempty"`
	DefaultInputModes  []string    `json:"defaultInputModes"`
	DefaultOutputModes []string    `json:"defaultOutputModes"`
	Skills            []AgentSkill `json:"skills"`
}

type AgentSkill struct {
	ID          string   `json:"id"`
	Name        string   `json:"name"`
	Description string   `json:"description,omitempty"`
	Tags        []string `json:"tags,omitempty"`
	Examples    []string `json:"examples,omitempty"`
}

type Provider struct {
	Organization string `json:"organization"`
}

type TaskStatus struct {
	State     string    `json:"state"`
	Message   *Message  `json:"message,omitempty"`
	Timestamp time.Time `json:"timestamp"`
}

type JSONRPCRequest struct {
	JSONRPC string      `json:"jsonrpc"`
	Method  string      `json:"method"`
	ID      string      `json:"id"`
	Params  interface{} `json:"params"`
}

type Artifact struct {
	Name  string     `json:"name,omitempty"`
	Parts []TextPart `json:"parts"`
	Index int        `json:"index,omitempty"`
}

type TaskResponse struct {
	JSONRPC string `json:"jsonrpc"`
	ID      string `json:"id"`
	Result  struct {
		ID       string     `json:"id"`
		Status   TaskStatus `json:"status,omitempty"`
		Artifact *Artifact  `json:"artifact,omitempty"`
		Final    bool       `json:"final"`
	} `json:"result"`
}

func colorize(color, text string) string {
	return color + text + colorReset
}

func fetchAgentCard(agentURL string) (*AgentCard, error) {
	resp, err := http.Get(agentURL + "/.well-known/agent.json")
	if err != nil {
		return nil, fmt.Errorf("failed to fetch agent card: %v", err)
	}
	defer resp.Body.Close()
	
	var card AgentCard
	if err := json.NewDecoder(resp.Body).Decode(&card); err != nil {
		return nil, fmt.Errorf("failed to decode agent card: %v", err)
	}
	
	return &card, nil
}

func handleStreamingResponse(resp *http.Response, card *AgentCard) {
	scanner := bufio.NewScanner(resp.Body)
	var lastResponse TaskResponse
	//var buffer strings.Builder

	// Create a channel to signal response is ready
	responseDone := make(chan bool)

	// Process the stream in a goroutine
	go func() {
		for scanner.Scan() {
			line := scanner.Text()
			if !strings.HasPrefix(line, "data: ") {
				continue
			}

			data := strings.TrimPrefix(line, "data: ")
			var response TaskResponse
			if err := json.Unmarshal([]byte(data), &response); err != nil {
				fmt.Printf("%s❌ Error parsing response: %v%s\n", colorRed, err, colorReset)
				continue
			}

			// Store the last response
			lastResponse = response
		}
		responseDone <- true
	}()

	// Wait for the response to be complete
	<-responseDone

	// Print the final formatted response
	if lastResponse.Result.ID != "" {
		timestamp := time.Now().Format("15:04:05")
		fmt.Printf("\n%s%s [%s]:%s", colorPurple, card.Name, timestamp, colorReset)

		// Print final status
		if lastResponse.Result.Status.State != "" {
			emoji := getStatusEmoji(lastResponse.Result.Status.State)
			stateColor := getStateColor(lastResponse.Result.Status.State)
			fmt.Printf(" %s %s%s%s\n", emoji, stateColor, lastResponse.Result.Status.State, colorReset)

			if lastResponse.Result.Status.Message != nil {
				for _, part := range lastResponse.Result.Status.Message.Parts {
					fmt.Printf("  %s%s%s\n", colorCyan, part.Text, colorReset)
				}
			}
		}

		// Print artifacts (currency conversion results)
		if lastResponse.Result.Artifact != nil {
			fmt.Printf("\n  %s📊 Result:%s\n", colorGreen, colorReset)
			for _, part := range lastResponse.Result.Artifact.Parts {
				fmt.Printf("  %s%s%s\n", colorCyan, part.Text, colorReset)
			}
		}

		if lastResponse.Result.Final {
			fmt.Printf("\n%s--- End of response ---%s\n\n", colorGray, colorReset)
		}
	}

	if err := scanner.Err(); err != nil {
		fmt.Printf("%s❌ Error reading response: %v%s\n", colorRed, err, colorReset)
	}
}

func getStatusEmoji(state string) string {
	switch state {
	case "working":
		return "⚙️"
	case "completed":
		return "✅"
	case "failed":
		return "❌"
	case "input-required":
		return "⌨️"
	default:
		return "❓"
	}
}

func getStateColor(state string) string {
	switch state {
	case "working":
		return colorBlue
	case "completed":
		return colorGreen
	case "failed":
		return colorRed
	case "input-required":
		return colorYellow
	default:
		return colorYellow
	}
}

func main() {
	agentURL := flag.String("agent", "http://localhost:10000", "URL of the A2A agent")
	flag.Parse()

	// Fetch agent card
	card, err := fetchAgentCard(*agentURL)
	if err != nil {
		log.Print(colorize(colorYellow, fmt.Sprintf("⚠️ Could not fetch agent card: %v", err)))
		card = &AgentCard{Name: "Agent"}
	} else {
		fmt.Printf("%s✓ Agent Card Found:%s\n", colorGreen, colorReset)
		fmt.Printf("  Name:        %s%s%s\n", "\033[1m", card.Name, colorReset)
		if card.Description != "" {
			fmt.Printf("  Description: %s\n", card.Description)
		}
		fmt.Printf("  Version:     %s\n", card.Version)
	}

	taskID := uuid.New().String()
	fmt.Printf("%sStarting Task ID: %s%s\n", colorGray, taskID, colorReset)
	fmt.Printf("%sEnter messages, or use '/new' to start a new task.%s\n", colorGray, colorReset)

	reader := bufio.NewReader(os.Stdin)
	for {
		fmt.Printf("%s%s > You:%s ", colorCyan, card.Name, colorReset)
		input, err := reader.ReadString('\n')
		if err != nil {
			if err == io.EOF {
				break
			}
			fmt.Printf("%s❌ Error reading input: %v%s\n", colorRed, err, colorReset)
			continue
		}

		input = strings.TrimSpace(input)
		if input == "" {
			continue
		}

		if input == "/new" {
			taskID = uuid.New().String()
			fmt.Printf("%s✨ Starting new Task ID: %s%s\n", "\033[1m", taskID, colorReset)
			continue
		}

		// Prepare the request
		req := JSONRPCRequest{
			JSONRPC: "2.0",
			Method:  "tasks/sendSubscribe",
			ID:      uuid.New().String(),
			Params: map[string]interface{}{
				"id":       taskID,
				"sessionId": uuid.New().String(),
				"acceptedOutputModes": []string{"text"},
				"message": Message{
					Role: "user",
					Parts: []TextPart{{
						Type: "text",
						Text: input,
					}},
				},
			},
		}

		// Send the request
		reqBody, _ := json.Marshal(req)
		resp, err := http.Post(*agentURL, "application/json", bytes.NewBuffer(reqBody))
		if err != nil {
			fmt.Printf("%s❌ Error sending request: %v%s\n", colorRed, err, colorReset)
			continue
		}

		// Handle the response
		handleStreamingResponse(resp, card)
		resp.Body.Close()
	}

	fmt.Printf("\n%sExiting terminal client. Goodbye!%s\n", colorYellow, colorReset)
}