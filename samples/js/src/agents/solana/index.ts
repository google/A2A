import {
  A2AServer,
  TaskContext,
  TaskYieldUpdate,
  schema,
} from "../../server/index.js";
import { MessageData } from "genkit";
import { ai } from "./genkit.js";
import { getBalance, getSlot } from "./tools.js";

if (!process.env.HEURIST_API_KEY || !process.env.SOLANA_RPC_URL) {
  console.error(
    "HEURIST_API_KEY, and SOLANA_RPC_URL environment variables are required"
  );
  process.exit(1);
}

const solanaPrompt = ai.prompt("solana_agent");

/**
 * Solana Agent Task Handler
 */
export async function* solanaAgentHandler(
  context: TaskContext
): AsyncGenerator<TaskYieldUpdate> {
  // Check if there is any message history
  if (!context.history || context.history.length === 0) {
    yield {
      state: "failed",
      message: {
        role: "agent",
        parts: [{ type: "text", text: "No messages to process." }],
      },
    };
    return;
  }

  const messages: MessageData[] = (context.history ?? [])
    .map((m) => ({
      role: (m.role === "agent" ? "model" : "user") as "user" | "model",
      content: m.parts
        .filter((p): p is schema.TextPart => !!(p as schema.TextPart).text)
        .map((p) => ({ text: p.text })),
    }))
    .filter((m) => m.content.length > 0);

  if (messages.length === 0) {
    yield {
      state: "failed",
      message: {
        role: "agent",
        parts: [{ type: "text", text: "No message found to process." }],
      },
    };
    return;
  }

  // Send the messages to the language model and yield the response
  try {
    const response = await solanaPrompt(
      { now: new Date().toISOString() },
      {
        messages,
        tools: [getSlot, getBalance],
      }
    );

    yield {
      state: "completed",
      message: {
        role: "agent",
        parts: [{ type: "text", text: response.text.trim() }],
      },
    };
  } catch (error: any) {
    yield {
      state: "failed",
      message: {
        role: "agent",
        parts: [
          {
            type: "text",
            text: `An error occurred while processing the request: ${error.message}`,
          },
        ],
      },
    };
  }
}

const solanaAgentCard: schema.AgentCard = {
  name: "Solana Agent",
  description: "Query Solana blockchain data via QuickNode.",
  url: "http://localhost:41241",
  provider: { organization: "QuickNode Agents" },
  version: "0.1.0",
  capabilities: {
    streaming: false,
    pushNotifications: false,
    stateTransitionHistory: true,
  },
  authentication: null,
  defaultInputModes: ["text"],
  defaultOutputModes: ["text"],
  skills: [
    {
      id: "solana_query",
      name: "Solana Blockchain Query",
      description: "Query data like slot number or wallet balance.",
      tags: ["solana", "blockchain", "rpc", "balance"],
      examples: [
        "What's the current Solana slot?",
        "Check wallet balance for 3aH1...XYZ",
      ],
    },
  ],
};

const server = new A2AServer(solanaAgentHandler, { card: solanaAgentCard });
server.start();
console.log("[SolanaAgent] Running at http://localhost:41241");
