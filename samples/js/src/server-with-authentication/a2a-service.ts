/**
 * Extension of the A2AServer class to represent an agent service that can be bundled with
 * other agent services in the same Express app.
 * 
 * This class adds AgentSessionResolver support, a general authentication helper that can inspect
 * request HTTP headers for authentication information, and generate HTTP responses (usually 401)
 * when appropriate.  This class overloads the Express Request object with an agentSession property
 * which the AgentSessionResolver provides.
 * 
 * Note that this class ignores the basePath option, as that should be specified when doing
 * app.use( basePath, a2aService.routes() )
 * 
 * @author: Mike Prince
 */

import express, {
  Request,
  Response,
  Router,
  NextFunction,
  RequestHandler,
} from "express";
import { ClientAgentSession } from "@agentic-profile/auth";

import { A2AServer, A2AServerOptions } from "../server/server.js";
import { normalizeError } from "../server/error.js";
import { TaskHandler } from "../server/handler.js";

/**
 * This function has three possible outcomes:
 * @return a ClientAgentSession which is usually attached as agentSession to the request object,
 *    or null to indicate the response has already been generated - usually with a 401 status and
 *    a challenge.
 * @throws an error when there is a problem processing the provided authentication, such as a
 *    malformed authentication, or a failure to fetch linked authentication information.
 */
export type AgentSessionResolver = ( req: Request, res: Response ) => Promise<ClientAgentSession | null>

/**
 * Extend the A2AServer options with an agentSessionResolver to handle authentication.
 */
export interface A2AServiceOptions extends A2AServerOptions {
  agentSessionResolver?: AgentSessionResolver
}

export class A2AService extends A2AServer {
  private agentSessionResolver: AgentSessionResolver | undefined;

  constructor(handler: TaskHandler, options: A2AServiceOptions = {}) {
    super( handler, options );
    if(options.basePath)
      console.warn("Ignoring agent basePath");
    this.agentSessionResolver = options.agentSessionResolver;
  }

  /**
   * Routes to add to the Express app, such as app.use( basePath, a2aService.routes() )
   */
  routes(): Router {
    const router = express.Router();
    router.post("/", this.endpoint());
    if( this.card ) {
      router.get("/agent.json", (req, res) => {
        res.json(this.card);
      });
    }
    return router;
  }

  /**
   * Returns an Express RequestHandler function to handle A2A requests.
   */
  endpoint(): RequestHandler {
    return async (req: Request, res: Response, next: NextFunction) => {
      // Authenticate client agent if agentSessionResolver provided
      if( this.agentSessionResolver ) {
        try {
            const agentSession = await this.agentSessionResolver( req, res );
            if( !agentSession ) {
              console.log( "Issued challenge to A2A client..." );
              return; // 401 response with challenge already issued
            }
            else {
              console.log( "Using A2A session", JSON.stringify(agentSession,null,4) );
              (req as any).agentSession = agentSession;   // overload req, add session
            }
        } catch (error) {
          // Forward errors to the Express error handler
          next(normalizeError(error, req.body?.id ?? null));
        }
      }

      // chain to A2AServer endpoint() handler
      const handler = super.endpoint();
      await handler( req, res, next );
    };
  }
}