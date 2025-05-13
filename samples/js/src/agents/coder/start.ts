import { A2AServer } from "../../server/index.js";
import { coderAgent, coderAgentCard } from "./index.js";

const server = new A2AServer(coderAgent, {
  card: coderAgentCard,
});

server.start(); // Default port 41241

console.log("[CoderAgent] Server started on http://localhost:41241");
console.log("[CoderAgent] Press Ctrl+C to stop the server");