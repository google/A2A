#!/usr/bin/env node

import readline from "node:readline";
import crypto from "node:crypto";
import { A2AClient } from "./client/client.js";
import {
  // Specific Params/Payload types used by the CLI
  TaskSendParams,
  TaskStatusUpdateEvent,
  TaskArtifactUpdateEvent,
  Message,
  // Other types needed for message/part handling
  FilePart,
  DataPart,
  // Type for the agent card
  AgentCard,
} from "./schema.js";

// --- ANSI Colors ---
const colors = {
  reset: "\x1b[0m",
  bright: "\x1b[1m",
  dim: "\x1b[2m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  magenta: "\x1b[35m",
  cyan: "\x1b[36m",
  gray: "\x1b[90m",
};

// --- Helper Functions ---
function colorize(color: keyof typeof colors, text: string): string {
  return `${colors[color]}${text}${colors.reset}`;
}

function generateTaskId(): string {
  return crypto.randomUUID();
}

// --- State ---
let currentTaskId: string = generateTaskId();
const serverUrl = process.argv[2] || "http://localhost:41241";
let agentName = "Agent"; // Default, try to get from agent card later

// --- Readline Setup ---
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  prompt: colorize("cyan", "You: "),
});

// --- Response Handling ---
// Function now accepts the unwrapped event payload directly
function printAgentEvent(
  event: TaskStatusUpdateEvent | TaskArtifactUpdateEvent
) {
  const timestamp = new Date().toLocaleTimeString();
  const prefix = colorize("magenta", `\n${agentName} [${timestamp}]:`);

  // Check if it's a TaskStatusUpdateEvent
  if ("status" in event) {
    const update = event as TaskStatusUpdateEvent; // Cast for type safety
    const state = update.status.state;
    let stateEmoji = "❓";
    let stateColor: keyof typeof colors = "yellow";

    switch (state) {
      case "working":
        stateEmoji = "⏳";
        stateColor = "blue";
        break;
      case "input-required":
        stateEmoji = "🤔";
        stateColor = "yellow";
        break;
      case "completed":
        stateEmoji = "✅";
        stateColor = "green";
        break;
      case "canceled":
        stateEmoji = "⏹️";
        stateColor = "gray";
        break;
      case "failed":
        stateEmoji = "❌";
        stateColor = "red";
        break;
    }

    console.log(
      `${prefix} ${stateEmoji} Status: ${colorize(stateColor, state)}`
    );

    if (update.status.message) {
      printMessageContent(update.status.message);
    }
  }
  // Check if it's a TaskArtifactUpdateEvent
  else if ("artifact" in event) {
    const update = event as TaskArtifactUpdateEvent; // Cast for type safety
    console.log(
      `${prefix} 📄 Artifact Received: ${
        update.artifact.name || "(unnamed)"
      } (Index: ${update.artifact.index ?? 0})`
    );
    printMessageContent({ role: "agent", parts: update.artifact.parts }); // Reuse message printing logic
  } else {
    // This case should ideally not happen if the stream yields correctly typed events
    console.log(
      prefix,
      colorize("yellow", "Received unknown event type:"),
      event
    );
  }
}

function printMessageContent(message: Message) {
  message.parts.forEach((part, index) => {
    const partPrefix = colorize("gray", `  Part ${index + 1}:`);
    if ("text" in part) {
      console.log(`${partPrefix} ${colorize("green", "📝 Text:")}`, part.text);
    } else if ("file" in part) {
      const filePart = part as FilePart;
      console.log(
        `${partPrefix} ${colorize("blue", "📄 File:")} Name: ${
          filePart.file.name || "N/A"
        }, Type: ${filePart.file.mimeType || "N/A"}, Source: ${
          filePart.file.bytes ? "Inline (bytes)" : filePart.file.uri
        }`
      );
      // Avoid printing large byte strings
      // if (filePart.file.bytes) {
      //     console.log(colorize('gray', `    Bytes: ${filePart.file.bytes.substring(0, 50)}...`));
      // }
    } else if ("data" in part) {
      const dataPart = part as DataPart;
      console.log(
        `${partPrefix} ${colorize("yellow", "📊 Data:")}`,
        JSON.stringify(dataPart.data, null, 2)
      );
    }
  });
}

// --- Agent Card Fetching ---
async function fetchAndDisplayAgentCard(): Promise<AgentCard> {
  const wellKnownUrl = new URL("/.well-known/agent.json", serverUrl).toString();
  console.log(
    colorize("dim", `Attempting to fetch agent card from: ${wellKnownUrl}`)
  );
  try {
    const response = await fetch(wellKnownUrl);
    if (response.ok) {
      const card: AgentCard = await response.json();
      agentName = card.name || "Agent"; // Update global agent name
      console.log(colorize("green", `✓ Agent Card Found:`));
      console.log(`  Name:        ${colorize("bright", agentName)}`);
      if (card.description) {
        console.log(`  Description: ${card.description}`);
      }
      console.log(`  Version:     ${card.version || "N/A"}`);
      // Update prompt prefix to use the fetched name
      rl.setPrompt(colorize("cyan", `${agentName} > You: `));

      return card;
    } else {
      console.log(
        colorize(
          "yellow",
          `⚠️ Could not fetch agent card (Status: ${response.status})`
        )
      );
    }
  } catch (error: any) {
    console.log(
      colorize("yellow", `⚠️ Error fetching agent card: ${error.message}`)
    );
  }
}

// --- Main Loop ---
async function main() {
  // Make main async
  console.log(colorize("bright", `A2A Terminal Client`));
  console.log(colorize("dim", `Agent URL: ${serverUrl}`));

  const agentCard = await fetchAndDisplayAgentCard(); // Fetch the card before starting the loop

  const client = new A2AClient(agentCard.url || serverUrl);

  console.log(colorize("dim", `Starting Task ID: ${currentTaskId}`));
  console.log(
    colorize("gray", `Enter messages, or use '/new' to start a new task.`)
  );

  rl.prompt(); // Start the prompt immediately

  rl.on("line", async (line) => {
    const input = line.trim();

    if (!input) {
      rl.prompt();
      return;
    }

    if (input.toLowerCase() === "/new") {
      currentTaskId = generateTaskId();
      console.log(
        colorize("bright", `✨ Starting new Task ID: ${currentTaskId}`)
      );
      rl.prompt();
      return;
    }

    // Construct just the params for the request
    const params: TaskSendParams = {
      // Use the specific Params type
      id: currentTaskId, // The actual Task ID
      message: {
        role: "user",
        parts: [{ type: "text", text: input }], // Ensure type: "text" is included if your schema needs it
      },
    };

    try {
      console.log(colorize("gray", "Sending...")); // Indicate request is sent
      // Pass only the params object to the client method
      const stream = client.sendTaskSubscribe(params);
      // Iterate over the unwrapped event payloads
      for await (const event of stream) {
        printAgentEvent(event); // Use the updated handler function
      }
      // Add a small visual cue that the stream for *this* message ended
      console.log(colorize("dim", `--- End of response for this input ---`));
    } catch (error: any) {
      console.error(
        colorize("red", `\n❌ Error communicating with agent (${agentName}):`),
        error.message || error
      );
      if (error.code) {
        console.error(colorize("gray", `   Code: ${error.code}`));
      }
      if (error.data) {
        console.error(
          colorize("gray", `   Data: ${JSON.stringify(error.data)}`)
        );
      }
    } finally {
      rl.prompt(); // Ensure prompt is always shown after processing
    }
  }).on("close", () => {
    console.log(colorize("yellow", "\nExiting terminal client. Goodbye!"));
    process.exit(0);
  });
}

// --- Start ---
main();
