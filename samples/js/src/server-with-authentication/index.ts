import 'dotenv/config';

import { setAgentHooks } from "@agentic-profile/common";

import { coderAgent } from "../agents/coder/index.js";
import { errorHandler } from "../server/error.js";

import { expressApp } from "./app.js";
import { A2AService } from "./a2a-service.js";
import { InMemoryStorage } from './in-memory-store.js';
import { createAgentSessionResolver } from "./agentic-auth.js";

/* Use default web DID resolver and in-memory agentic-profile cache */
setAgentHooks({});  

/* Publish www/ directory with agent cards and agentic profiles for testing */
const app = expressApp({ wwwDir: ["www"] });


//==== Example 1: A2A agent with no authentication ====
const a2aService1 = new A2AService( coderAgent, {} );
app.use("/agents/coder", a2aService1.routes() );


//==== Example 2: A2A agent with authentication ====
const a2aService2 = new A2AService( coderAgent, {
    agentSessionResolver: createAgentSessionResolver( new InMemoryStorage() )
});
app.use("/users/:uid/coder", a2aService2.routes() );


// Basic error handler for a2a services
app.use( errorHandler );

const port = process.env.PORT || 41241;
app.listen(port, () => {
    console.info(`Agentic Profile Express listening on http://localhost:${port}`);
});