import { GenkitBeta, z } from "genkit/beta";

export const EmailMessageSchema = z.object({
  fromname: z.string(),
  fromemail: z.string().email().optional(),
  to: z.string().email(),
  toname: z.string().optional(),
  subject: z.string(),
  body: z.string(),
  replyto: z.string().email().optional(),
  returnpath: z.string().email().optional(),
  tag: z.string().optional(),
  variables: z.record(z.any()).optional(),
  route: z.string().optional(),
  template: z.string().optional()
});

export type EmailMessageData = z.infer<typeof EmailMessageSchema>;

export class EmailMessage implements EmailMessageData {
  fromname: string;
  fromemail?: string;
  to: string;
  toname?: string;
  subject: string;
  body: string;
  replyto?: string;
  returnpath?: string;
  tag?: string;
  variables?: Record<string, any>;
  route?: string;
  template?: string;

  constructor(data: EmailMessageData) {
    this.fromname = data.fromname;
    this.fromemail = data.fromemail;
    this.to = data.to;
    this.toname = data.toname;
    this.subject = data.subject;
    this.body = data.body;
    this.replyto = data.replyto;
    this.returnpath = data.returnpath;
    this.tag = data.tag;
    this.variables = data.variables;
    this.route = data.route;
    this.template = data.template;
  }

  toJSON(): EmailMessageData {
    return {
      fromname: this.fromname,
      fromemail: this.fromemail,
      to: this.to,
      toname: this.toname,
      subject: this.subject,
      body: this.body,
      replyto: this.replyto,
      returnpath: this.returnpath,
      tag: this.tag,
      variables: this.variables,
      route: this.route,
      template: this.template
    };
  }
}

function parseEmailData(text: string): EmailMessageData {
  try {
    // First check if the text is already valid JSON
    try {
      const parsedJson = JSON.parse(text);
      if (parsedJson && typeof parsedJson === 'object') {
        return parsedJson;
      }
    } catch (e) {
      // Not valid JSON, continue with parsing
    }
    
    // Extract email fields from text format
    const fromMatch = text.match(/From:[\s\n]*(.*?)[\s\n]*<(.*?)>/i);
    const toMatch = text.match(/To:[\s\n]*(.*?)[\s\n]*<(.*?)>/i);
    const subjectMatch = text.match(/Subject:[\s\n]*(.*?)(?:\n|$)/i);
    
    // Extract body - everything after first blank line
    const bodyStart = text.indexOf("\n\n");
    const body = bodyStart !== -1 ? text.substring(bodyStart + 2).trim() : "";
    
    // Extract tag if present
    const tagMatch = text.match(/Tag:[\s\n]*(.*?)(?:\n|$)/i);
    
    // Extract variables if present - try to find a JSON block
    const variablesMatch = text.match(/Variables:[\s\n]*([\s\S]*?)(?:\n\n|$)/i);
    let variables: Record<string, any> = {};
    if (variablesMatch && variablesMatch[1]) {
      try {
        variables = JSON.parse(variablesMatch[1].trim());
      } catch (e) {
        // If not valid JSON, try to parse key-value pairs
        const varText = variablesMatch[1];
        const varPairs = varText.split(/[,\n]/);
        varPairs.forEach(pair => {
          const [key, value] = pair.split(':').map(s => s.trim());
          if (key && value) {
            variables[key] = value;
          }
        });
      }
    }
    
    return {
      fromname: fromMatch ? fromMatch[1].trim() : "Default Sender",
      fromemail: fromMatch ? fromMatch[2].trim() : "mail@member-notification.com",
      to: toMatch ? toMatch[2].trim() : "recipient@example.com",
      toname: toMatch ? toMatch[1].trim() : undefined,
      subject: subjectMatch ? subjectMatch[1].trim() : "No Subject",
      body: body || "Empty email body",
      tag: tagMatch ? tagMatch[1].trim() : undefined,
      variables: Object.keys(variables).length > 0 ? variables : undefined
    };
  } catch (error) {
    console.error("Error parsing email data:", error);
    throw new Error("Failed to parse email format");
  }
}

export function defineEmailFormat(ai: GenkitBeta) {
  return ai.defineFormat(
    {
      name: "email",
      contentType: "application/json",
      format: "text",
      schema: EmailMessageSchema,
    },
    () => {
      return {
        instructions: `\n\n=== Output Instructions

Please provide the email details in the following format:

From: [Sender Name] <[sender@email.com]>
To: [Recipient Name] <[recipient@email.com]>
Subject: [Email Subject]
Tag: [Optional Tag for categorizing this email]

[Email Body in HTML format]

If you need to include template variables, include them in a Variables section:

Variables:
{
  "username": "johndoe",
  "resetLink": "https://example.com/reset",
  "companyName": "ACME Corp"
}

If you don't specify a sender email, "mail@member-notification.com" will be used as the default.
The email body can include HTML formatting for rich content. Use appropriate HTML tags for headers, paragraphs, links, etc.
`,
        parseMessage: (message: { text: string }) => {
          return new EmailMessage(parseEmailData(message.text));
        },
        parseChunk: (chunk: { accumulatedText: string }) => {
          return new EmailMessage(parseEmailData(chunk.accumulatedText));
        },
      };
    }
  );
}