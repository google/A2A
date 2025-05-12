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
    // More flexible regex patterns that can handle variations in formatting
    const fromMatch = text.match(/From:[\s\n]*(.*?)(?:<(.*?)>)?(?:\n|$)/i);
    const toMatch = text.match(/To:[\s\n]*(.*?)(?:<(.*?)>)?(?:\n|$)/i);
    const subjectMatch = text.match(/Subject:[\s\n]*(.*?)(?:\n|$)/i);
    
    // Extract email addresses directly if the format doesn't include angle brackets
    const extractEmail = (str?: string): string | undefined => {
      if (!str) return undefined;
      
      const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/;
      const match = str.match(emailRegex);
      return match ? match[0] : str;
    };
    
    let fromName = fromMatch?.[1]?.trim() || "Default Sender";
    let fromEmail = fromMatch?.[2]?.trim();
    
    if (!fromEmail && fromMatch?.[1]) {
      // Check if the "From" field contains an email without angle brackets
      fromEmail = extractEmail(fromMatch[1]);
      if (fromEmail && fromEmail !== fromMatch[1]) {
        // If we extracted an email, the rest might be the name
        fromName = fromMatch[1].replace(fromEmail, "").trim();
      }
    }
    
    let toName = toMatch?.[1]?.trim() || "";
    let toEmail = toMatch?.[2]?.trim();
    
    if (!toEmail && toMatch?.[1]) {
      // Check if the "To" field contains an email without angle brackets
      toEmail = extractEmail(toMatch[1]);
      if (toEmail && toEmail !== toMatch[1]) {
        // If we extracted an email, the rest might be the name
        toName = toMatch[1].replace(toEmail, "").trim();
      }
    }
    
    // If we still don't have a recipient email, look for any email in the entire text
    if (!toEmail) {
      const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
      const allEmails = text.match(emailRegex) || [];
      
      // Skip the fromEmail if we already identified it
      if (allEmails.length > 0) {
        if (!fromEmail || allEmails[0] !== fromEmail) {
          toEmail = allEmails[0];
        } else if (allEmails.length > 1) {
          toEmail = allEmails[1];
        }
      }
    }
    
    // Extract body - everything after first blank line or after the headers
    let bodyStart = text.indexOf("\n\n");
    if (bodyStart === -1) {
      // No blank line found, look for the end of the headers
      const headerSections = [
        text.indexOf("\nFrom:"),
        text.indexOf("\nTo:"),
        text.indexOf("\nSubject:"),
        text.indexOf("\nTag:"),
        text.indexOf("\nVariables:")
      ].filter(pos => pos !== -1);
      
      const lastHeader = Math.max(...headerSections);
      const nextLineBreak = text.indexOf("\n", lastHeader + 1);
      
      if (nextLineBreak !== -1) {
        bodyStart = nextLineBreak;
      } else {
        bodyStart = text.length;
      }
    }
    
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
      fromname: fromName,
      fromemail: fromEmail || "mail@member-notification.com",
      to: toEmail,
      toname: toName || undefined,
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