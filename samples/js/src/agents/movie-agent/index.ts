import {
  A2AServer,
  TaskContext,
  TaskYieldUpdate,
  schema
} from "../../server/index.js";
import { MessageData } from "genkit";
import { ai } from "./genkit.js";
import { searchMovies, searchPeople } from "./tools.js";

if (!process.env.GEMINI_API_KEY || !process.env.TMDB_API_KEY) {  
  console.error("GEMINI_API_KEY and TMDB_API_KEY environment variables are required")
  process.exit(1);
}

// Load the prompt defined in movie_agent.prompt
const movieAgentPrompt = ai.prompt("movie_agent");

/**
 * Task Handler for the Movie Agent.
 */
async function* movieAgentHandler(
  context: TaskContext
): AsyncGenerator<TaskYieldUpdate> {
  console.log(
    `[MovieAgent] Processing task ${context.task.id} with state ${context.task.status.state}`
  );

  // Yield an initial "working" status
  yield {
    state: "working",
    message: {
      role: "agent",
      parts: [{ type:"text", text: "Processing your question, hang tight!" }],
    },
  };

  // Prepare messages for Genkit prompt using the full history from context
  const messages: MessageData[] = (context.history ?? []) // Use history if available, default to empty array
    .map((m) => ({
      // Map roles explicitly and assert the type for Genkit
      role: (m.role === "agent" ? "model" : "user") as "user" | "model",
      content: m.parts
        .filter((p): p is schema.TextPart => !!(p as schema.TextPart).text) // Filter for text parts
        .map((p) => ({
          text: p.text,
        })),
    }))
    // Filter out messages with no text content after mapping
    .filter((m) => m.content.length > 0);

  // Add a check in case history was empty or only contained non-text parts
  if (messages.length === 0) {
    console.warn(
      `[MovieAgent] No valid text messages found in history for task ${context.task.id}. Cannot proceed.`
    );
    yield {
      state: "failed",
      message: {
        role: "agent",
        parts: [{ type:"text", text: "No message found to process." }],
      },
    };
    return; // Stop processing
  }

  // Include the goal from the initial task metadata if available
  const goal = context.task.metadata?.goal as string | undefined;

  try {
    // Run the Genkit prompt
    const response = await movieAgentPrompt(
      { goal: goal, now: new Date().toISOString() }, // Pass goal from metadata
      {
        messages,
        tools: [searchMovies, searchPeople],
      }
    );

    const responseText = response.text; // Access the text property directly
    const lines = responseText.trim().split("\n");
    const finalStateLine = lines.at(-1)?.trim().toUpperCase(); // Get last line, uppercase for robust comparison
    const agentReply = lines
      .slice(0, lines.length - 1)
      .join("\n")
      .trim(); // Get all lines except the last

    let finalState: schema.TaskState = "unknown";

    // Map prompt output instruction to A2A TaskState
    if (finalStateLine === "COMPLETED") {
      finalState = "completed";
    } else if (finalStateLine === "AWAITING_USER_INPUT") {
      finalState = "input-required";
    } else {
      console.warn(
        `[MovieAgent] Unexpected final state line from prompt: ${finalStateLine}. Defaulting to 'completed'.`
      );
      // If the LLM didn't follow instructions, default to completed
      finalState = "completed";
    }

    // Yield the final result
    yield {
      state: finalState,
      message: {
        role: "agent",
        parts: [{ type: "text", text: agentReply }],
      },
    };

    console.log(
      `[MovieAgent] Task ${context.task.id} finished with state: ${finalState}`
    );
  } catch (error: any) {
    console.error(
      `[MovieAgent] Error processing task ${context.task.id}:`,
      error
    );
    // Yield a failed state if the prompt execution fails
    yield {
      state: "failed",
      message: {
        role: "agent",
        parts: [{ type: "text", text: `Agent error: ${error.message}` }],
      },
    };
  }
}

// --- Server Setup ---

const movieAgentCard: schema.AgentCard = {
  name: "Movie Agent",
  description:
    "An agent that can answer questions about movies and actors using TMDB.",
  url: "http://localhost:41241", // Default port used in the script
  provider: {
    organization: "A2A Samples",
  },
  version: "0.0.1",
  capabilities: {
    // Although it yields multiple updates, it doesn't seem to implement full A2A streaming via TaskYieldUpdate artifacts
    // It uses Genkit streaming internally, but the A2A interface yields start/end messages.
    // State history seems reasonable as it processes history.
    streaming: false,
    pushNotifications: false,
    stateTransitionHistory: true,
  },
  authentication: null,
  defaultInputModes: ["text"],
  defaultOutputModes: ["text"],
  skills: [
    {
      id: "general_movie_chat",
      name: "General Movie Chat",
      description:
        "Answer general questions or chat about movies, actors, directors.",
      tags: ["movies", "actors", "directors"],
      examples: [
        "Tell me about the plot of Inception.",
        "Recommend a good sci-fi movie.",
        "Who directed The Matrix?",
        "What other movies has Scarlett Johansson been in?",
        "Find action movies starring Keanu Reeves",
        "Which came out first, Jurassic Park or Terminator 2?",
      ],
    },
    // The specific tools are used internally by the Genkit agent,
    // but from the A2A perspective, it exposes one general chat skill.
  ],
};

// Create server with the task handler. Defaults to InMemoryTaskStore.
const server = new A2AServer(movieAgentHandler, { card: movieAgentCard });

// Start the server
server.start(); // Defaults to port 41241

console.log("[MovieAgent] Server started on http://localhost:41241");
console.log("[MovieAgent] Press Ctrl+C to stop the server");
