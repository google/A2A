/**
 * Enhanced Agent Card support, providing global agent identity
 * and decentralized authentication using W3C DID documents.
 * 
 * An agent can be specified by:
 * - a "well-known" agent service and card URL, e.g. http://example.com
 * - the absolute agent card URL, e.g. http://example.com/agents/coder/agent.json
 * - the agent service endpoint, e.g. http://example.com/agents/coder/
 * - the user or business DID, e.g. did:web:example.com:iam:mike#coder
 * - the user or business "well-known" DID, e.g. did:web:example.com#coder
 */

import {
  AgenticProfile,
  pruneFragmentId,
  webDidToUrl
} from "@agentic-profile/common";
import { getJson } from "@agentic-profile/auth";

import { AgentCard } from "../schema.js";

/**
 * Full or partial context for an agent.
 * If the agent was specified with a DID, then the Agentic Profile (DID document)
 * is provided along with the agent card and agent card url.
 */
export interface AgentContext {
  profileUrl?: string,
  agenticProfile?: AgenticProfile,
  agentCardUrl: string,
  agentCard: AgentCard  
}

/**
 * Fetch the agent card
 *  - if URL is DID protocol, fetch agentic profile, then resolve agent from service[]
 *  - if URL is HTTP/HTTPS then fetch agent card from:
 *      - existing URL if it ends with "/agent.json"
 *      - /.well-known/agent.json if the URL pathname is "/"
 *      - the agent.json in the same directory as the agent endpoint
 * @param agentUrl
 * @return The agent context
 */
export async function resolveAgent( agentUrl: string ): Promise<AgentContext> {
  let profileUrl: string | undefined;
  let agenticProfile: AgenticProfile | undefined;

  let url = new URL( agentUrl );
  if( url.protocol === "did:" ) {
    // ensure we have the fragment id to find the agent
    const { fragmentId } = pruneFragmentId( agentUrl );
    if( !fragmentId )
      throw new Error(`Agentic profile DID is missing the fragment to resolve the agent ${agentUrl}`);

    // fetch the DID document/agentic profile
    profileUrl = webDidToUrl( agentUrl );
    ({ data: agenticProfile } = await getJson( profileUrl! ));

    // find agent
    const agent = agenticProfile!.service?.find(e=>e.id === fragmentId);
    if( !agent )
      throw new Error(`Failed to find agent ${fragmentId} from agentic profile at ${profileUrl}`);
    if( agent.type?.toLowerCase() !== "a2a" )
      throw new Error(`Agent type is not A2A, instead it is ${agent.type}`);

    agentUrl = Array.isArray( agent.serviceEndpoint ) ? agent.serviceEndpoint[0] as string : agent.serviceEndpoint as string;
    if( !agentUrl )
      throw new Error(`Agent ${fragmentId} from ${profileUrl} is missing the serviceEndpoint`);
    url = new URL( agentUrl );
  }

  // fixup agentUrl to find agent card
  let agentCardUrl: string;
  if( url.pathname.endsWith("/agent.json") ) {
    agentCardUrl = url.toString();
  } else if( url.pathname === "/" ) {
    agentCardUrl = new URL("/.well-known/agent.json", agentUrl).toString();    
  } else {
    // try to find agent card in same directory as agent service endpoint
    agentCardUrl = new URL("agent.json",agentUrl).toString();
  }

  const { data: agentCard } = await getJson( agentCardUrl );

  return {
    profileUrl,
    agenticProfile,
    agentCardUrl,
    agentCard
  };
}


/**
 * Optional: Checks if the server likely supports optional methods based on agent card.
 * This is a client-side heuristic and might not be perfectly accurate.
 * @param card Agent card to check
 * @param capability The capability to check (e.g., 'streaming', 'pushNotifications').
 * @returns True if the capability is likely supported.
 */
export function supports( card: AgentCard, capability: "streaming" | "pushNotifications"): boolean {
  switch (capability) {
    // Check boolean flags directly on the capabilities object
    case "streaming":
      return !!card.capabilities?.streaming; // Use optional chaining and boolean conversion
    case "pushNotifications":
      return !!card.capabilities?.pushNotifications; // Use optional chaining and boolean conversion
    default:
      return false;
  }
}