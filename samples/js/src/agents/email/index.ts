import { MessageData } from "genkit";
import { TaskYieldUpdate } from "../../server/handler.js";
import {
  TaskContext,
  A2AServer,
} from "../../server/index.js";
import * as schema from "../../schema.js";
import { ai } from "./genkit.js";
import { EmailMessage } from "./email-format.js";

// Check for API key
if (!process.env.GEMINI_API_KEY) {  
  console.error("GEMINI_API_KEY environment variable not set.")
  process.exit(1);
}

// Check for Lemon API key
if (!process.env.LEMON_API_KEY) {
  console.error("LEMON_API_KEY environment variable not set.");
  process.exit(1);
}

// Configuration
const apiBaseUrl = process.env.Lemon_API_URL || "https://app.xn--lemn-sqa.com/api";

interface EmailResponse {
  id?: string;
  success?: boolean;
  [key: string]: any;
}

// Extract email addresses from text
function extractEmailsFromText(text: string): string[] {
  const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
  return text.match(emailRegex) || [];
}

// Analyze request type
function analyzeRequestType(text: string): string {
  if (/welcome/i.test(text)) return "welcome";
  if (/confirm/i.test(text)) return "confirmation";
  if (/invit(e|ation)/i.test(text)) return "invitation";
  if (/reset|password/i.test(text)) return "password_reset";
  if (/thank/i.test(text)) return "thank_you";
  if (/notify|notification/i.test(text)) return "notification";
  return "general"; // Default fallback
}

// function to check for inappropriate content
function screenForInappropriateContent(text: string): boolean {
  const inappropriateTerms = [
    'stupid', 'idiot', 'dumb', 'moron', 'fool', 
    'offensive', 'inappropriate', 'hate', 'insult',
    // Add more terms as needed
  ];
  
  const lowerText = text.toLowerCase();
  return inappropriateTerms.some(term => lowerText.includes(term));
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

  // Extract user's last message to check for email addresses
  const lastUserMessage = messages.findLast(m => m.role === "user");
  if (!lastUserMessage || !lastUserMessage.content[0]?.text) {
    yield {
      state: "failed",
      message: {
        role: "agent",
        parts: [{ text: "No valid user message found." }],
      },
    };
    return;
  }
  
  const lastUserText = lastUserMessage.content[0].text;
  
  // Check if there are any email addresses in the user's message
  const emailsInMessage = extractEmailsFromText(lastUserText);
  
  // If no email found in the message, prompt user to provide one
  if (emailsInMessage.length === 0) {
    yield {
      state: "failed",
      message: {
        role: "agent",
        parts: [{ 
          type: "text", 
          text: "I couldn't find any email address in your request. Please include a valid email address for the recipient." 
        }],
      },
    };
    return;
  }
  
  // Use the first email as the recipient
  const recipientEmail = emailsInMessage[0];
  // Extract recipient name from email
  const recipientName = recipientEmail.split('@')[0].replace(/[^a-zA-Z]/g, ' ').trim();
  
  yield {
    state: "working",
    message: {
      role: "agent",
      parts: [{ type: "text", text: `Processing email request for ${recipientEmail}...` }],
    },
  };

  // Determine email type based on user request
  const emailType = analyzeRequestType(lastUserText);

  if (screenForInappropriateContent(lastUserText)) {
    yield {
      state: "failed",
      message: {
        role: "agent",
        parts: [{ 
          type: "text", 
          text: "I cannot process this request as it appears to contain inappropriate or offensive content. Please provide a respectful email request." 
        }],
      },
    };
    return;
  }
  
  try {
    // First - generate just the subject line
    const { response: subjectResponse } = await ai.generateStream({
      system: `You are an email assistant. Based on the user's request, generate ONLY an appropriate subject line for an email of type: ${emailType}.
      Respond with ONLY the subject line text, nothing else.`,
      messages: [...messages]
    });
    
    let subjectText;
    try {
      const subjectResponseResult = await subjectResponse;
      subjectText = typeof subjectResponseResult.text === 'function' 
        ? subjectResponseResult.text().trim() 
        : subjectResponseResult.text.trim();
    } catch (err) {
      console.error("[EmailAgent] Error extracting subject:", err);
      subjectText = `${emailType.charAt(0).toUpperCase() + emailType.slice(1)} Email`;
    }
    
    // Second - generate the email body content
    const { response: bodyResponse } = await ai.generateStream({
      system: `You are an email assistant. Based on the user's request, generate ONLY the body content for an email of type: ${emailType}.
      The email is being sent to ${recipientName ? recipientName : "the recipient"} (${recipientEmail}).
      Respond with ONLY the HTML-formatted body content, nothing else. Include appropriate greeting and signature.`,
      messages: [...messages]
    });
    
    let bodyText = (await bodyResponse).text;
    
    // Ensure the body has HTML formatting
    if (!bodyText.includes('<p>') && !bodyText.includes('<div>')) {
      bodyText = bodyText.split('\n\n').map(para => `<p>${para}</p>`).join('');
    }
    
    console.log("[EmailAgent] Generated body length:", bodyText.length);
    
    // Create the email data
    const emailData = new EmailMessage({
      fromname: "Email Assistant",
      fromemail: "mail@member-notification.com",
      to: recipientEmail,
      subject: subjectText || `${emailType.charAt(0).toUpperCase() + emailType.slice(1)} Email`,
      body: bodyText || `<p>Dear ${recipientName || "User"},</p><p>This is a ${emailType} email from our service.</p><p>Thank you,<br>Email Assistant</p>`
    });
    
    console.log("[EmailAgent] Prepared email data:", {
      to: emailData.to,
      subject: emailData.subject,
      bodyLength: emailData.body?.length || 0
    });

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
    console.error("[EmailAgent] Error:", error);
    yield {
      state: "failed",
      message: {
        role: "agent",
        parts: [{ 
          type: "text", 
          text: `Failed to send email: ${error instanceof Error ? error.message : String(error)}. Please try again with a more specific instruction.` 
        }],
      },
    };
  }
}

// Function to send email using the API
async function sendEmail(emailData: EmailMessage): Promise<EmailResponse> {
  try {
    // Final validation to ensure we have the required fields
    if (!emailData.to || !emailData.to.includes('@')) {
      throw new Error("Missing valid recipient email address");
    }
    
    if (!emailData.subject || emailData.subject.trim() === '') {
      throw new Error("Missing email subject");
    }
    
    if (!emailData.body || emailData.body.trim() === '') {
      throw new Error("Missing email body content");
    }

    const emailPayload = {
      fromname: emailData.fromname || 'Email Assistant',
      fromemail: emailData.fromemail || 'mail@member-notification.com',
      to: emailData.to,
      toname: emailData.toname || '',
      subject: emailData.subject,
      body: emailData.body,
      tag: emailData.tag || 'a2a-agent',
      variables: emailData.variables || {},
      replyto: emailData.replyto || emailData.fromemail || 'mail@member-notification.com'
    };

    console.log("[EmailAgent] Sending email with payload:", {
      to: emailPayload.to,
      subject: emailPayload.subject,
      fromname: emailPayload.fromname,
      bodyLength: emailPayload.body.length
    });

    const response = await fetch(`${apiBaseUrl}/transactional/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Auth-APIKey': process.env.LEMON_API_KEY || ''
      },
      body: JSON.stringify(emailPayload)
    });
    
    const responseText = await response.text();
    
    if (!response.ok) {
      throw new Error(`API error ${response.status}: ${responseText}`);
    }
    
    // Parse the response JSON if possible
    let responseData: EmailResponse;
    try {
      responseData = JSON.parse(responseText);
    } catch (e) {
      responseData = { success: true, id: 'unknown' };
    }
    
    return responseData;
  } catch (error) {
    console.error("[EmailAgent] Error with API:", error);
    throw new Error(`API error: ${error instanceof Error ? error.message : String(error)}`);
  }
}

// --- Server Setup ---

const emailAgentCard: schema.AgentCard = {
  name: "Lemon Email Agent",
  description: "An agent that sends emails via Lemon API based on natural language instructions.",
  url: "http://localhost:41242", // Default port used in the script
  provider: {
    organization: "Lemon A2A",
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
      description: "Sends emails via Lemon API based on user requests and instructions.",
      tags: ["email", "communication", "Lemon"],
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