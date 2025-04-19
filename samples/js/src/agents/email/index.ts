import { MessageData } from "genkit";
import { TaskYieldUpdate } from "../../server/handler.js";
import {
  TaskContext,
  A2AServer,
  InMemoryTaskStore,
} from "../../server/index.js";
import * as schema from "../../schema.js";
import { ai } from "./genkit.js";
import { EmailMessage } from "./email-format.js";

// Check for API key
if (!process.env.GEMINI_API_KEY) {  
  console.error("GEMINI_API_KEY environment variable not set.")
  process.exit(1);
}

// Check for Lemn API key
if (!process.env.LEMN_API_KEY) {
  console.error("LEMN_API_KEY environment variable not set.");
  process.exit(1);
}

// Configuration
const apiBaseUrl = process.env.LEMN_API_URL || "https://app.xn--lemn-sqa.com/api";

interface EmailResponse {
  id?: string;
  success?: boolean;
  [key: string]: any;
}

async function* emailAgent({
  task,
  history,
}: TaskContext): AsyncGenerator<TaskYieldUpdate, schema.Task | void, unknown> {
  // Map A2A history to Genkit messages
  const messages: MessageData[] = (history ?? [])
    .map((m) => ({
      role: (m.role === "agent" ? "model" : "user") as "user" | "model",
      content: m.parts
        .filter((p): p is schema.TextPart => !!(p as schema.TextPart).text)
        .map((p) => ({ text: p.text })),
    }))
    .filter((m) => m.content.length > 0);

  if (messages.length === 0) {
    console.warn(`[EmailAgent] No history/messages found for task ${task.id}`);
    yield {
      state: "failed",
      message: {
        role: "agent",
        parts: [{ text: "No input message found." }],
      },
    };
    return;
  }

  yield {
    state: "working",
    message: {
      role: "agent",
      parts: [{ type: "text", text: "Processing your email request..." }],
    },
  };

  const { response } = await ai.generateStream({
    system:
      "You are an expert email assistant. Given a user's request, you'll craft an appropriate email or response. Your output should follow the email schema format.",
    output: { format: "email" },
    messages,
  });

  const emailData = (await response).output as EmailMessage;
  
  if (!emailData) {
    yield {
      state: "failed",
      message: {
        role: "agent",
        parts: [{ type: "text", text: "Failed to generate email data." }],
      },
    };
    return;
  }

  try {
    // Send the email using the API
    const result = await sendEmail(emailData);
    
    yield {
      state: "completed",
      message: {
        role: "agent",
        parts: [
          {
            type: "text",
            text: `Email sent successfully to ${emailData.to}!\n\nSubject: ${emailData.subject}\n\nEmail ID: ${result.id || 'N/A'}`
          },
        ],
      },
    };
  } catch (error) {
    console.error("[EmailAgent] Error sending email:", error);
    yield {
      state: "failed",
      message: {
        role: "agent",
        parts: [{ 
          type: "text", 
          text: `Failed to send email: ${error instanceof Error ? error.message : String(error)}` 
        }],
      },
    };
  }
}

// Function to send email using the API
async function sendEmail(emailData: EmailMessage): Promise<EmailResponse> {
  try {
    const response = await fetch(`${apiBaseUrl}/transactional/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Auth-APIKey': process.env.LEMN_API_KEY
      },
      body: JSON.stringify({
        fromname: emailData.fromname,
        fromemail: emailData.fromemail || 'mail@member-notification.com',
        to: emailData.to,
        toname: emailData.toname || '',
        subject: emailData.subject,
        body: emailData.body,
        tag: emailData.tag || 'a2a-agent',
        variables: emailData.variables || {},
        replyto: emailData.replyto || emailData.fromemail || 'mail@member-notification.com'
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(`API error ${response.status}: ${JSON.stringify(errorData)}`);
    }
    
    return await response.json() as EmailResponse;
  } catch (error) {
    console.error("[EmailAgent] Error with API:", error);
    throw new Error(`API error: ${error instanceof Error ? error.message : String(error)}`);
  }
}

// --- Server Setup ---

const emailAgentCard: schema.AgentCard = {
  name: "Lemn Email Agent",
  description: "An agent that sends emails via Lemn API based on natural language instructions.",
  url: "http://localhost:41242", // Default port used in the script
  provider: {
    organization: "Lemn A2A",
  },
  version: "0.0.1",
  capabilities: {
    streaming: false, // Not streaming artifacts
    pushNotifications: false,
    stateTransitionHistory: true, // Uses history for context
  },
  authentication: null, // No auth mentioned
  defaultInputModes: ["text"],
  defaultOutputModes: ["text"], // Outputs status as text
  skills: [
    {
      id: "email_sending",
      name: "Email Sending",
      description: "Sends emails via Lemn API based on user requests and instructions.",
      tags: ["email", "communication", "lemn"],
      examples: [
        "Send a welcome email to john@example.com",
        "Draft an invoice confirmation email to client@company.com",
        "Send a password reset notification to user@domain.com",
        "Create a meeting invitation email for the team",
        "Send a thank you email to our recent customers",
      ],
    },
  ],
};

const server = new A2AServer(emailAgent, {
  card: emailAgentCard,
});

server.start();

console.log("[EmailAgent] Server started on http://localhost:41242");
console.log("[EmailAgent] Press Ctrl+C to stop the server");