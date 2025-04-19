# Lemn Email Agent

This is an A2A agent that sends emails via the Lemn API. It can process natural language requests to create and send emails through the Lemn API.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Set required environment variables:
```bash
export GEMINI_API_KEY=<your_gemini_api_key>
export LEMN_API_KEY=<your_lemn_api_key>
```

3. Start the agent:
```bash
npm run agents:email
```

This will start up the agent on `http://localhost:41241/`.

## Usage

You can interact with this agent via the A2A protocol. Simply send requests with instructions about what kind of email you want to send. For example:

- "Send a welcome email to john@example.com"
- "Draft an invoice confirmation email to client@company.com"
- "Send a password reset notification to user@domain.com"

The agent will handle generating appropriate email content and sending it through the Lemn API.

## Notes

- The agent uses the Lemn REST API directly
- If no sender email is specified in the request, the default sender email `mail@member-notification.com` will be used
- All emails will be tagged with 'a2a-agent' by default unless a specific tag is provided

## Integration

To add this agent to the A2A sample project:

1. Place these files in the `src/agents/email` directory
2. Add an entry to `package.json` scripts:
   ```json
   "agents:email": "tsx src/agents/email/index.ts"
   ```
3. Ensure you have the required environment variables set before running