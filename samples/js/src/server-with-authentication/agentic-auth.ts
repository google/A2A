import {
  Response,
  Request
} from "express";
import {
  ClientAgentSession,
  ClientAgentSessionStorage,
  createChallenge,
  handleAuthorization,
} from "@agentic-profile/auth";

/**
 * Creates an agent session resolver that handles an Express request.
 * @param storage Session storage service. 
 */
export function createAgentSessionResolver( storage: ClientAgentSessionStorage ) {

  /**
   * Process an Express request/response pair and handle authorization.
   * @param req Express Request
   * @param res Express Response
   * @return a ClientAgentSession if authentication with a JWT succeeded, or null if no JWT was provided and a 401 response was issued.
   * @throws an Error if the JWT was provided but there were errors processing it.
   */ 
  return async ( req: Request, res: Response ): Promise<ClientAgentSession | null> => {
    const { authorization } = req.headers;
    if( authorization )
      return await handleAuthorization( authorization, storage );

    const challenge = await createChallenge( storage );
    res.status(401)
      .set('Content-Type', 'application/json')
      .send( JSON.stringify(challenge,null,4) );
    return null;  
  }
}
