import {
  AgenticProfile,
  DID
} from "@agentic-profile/common";
import {
  ClientAgentSession,
  ClientAgentSessionStorage,
  ClientAgentSessionUpdates
} from "@agentic-profile/auth";

let nextSessionId = 1;
const clientSessions = new Map<number,ClientAgentSession>();

const profileCache = new Map<string,AgenticProfile>();

function mapToObject<K extends PropertyKey, V>(map: Map<K, V>): Record<K, V> {
  return Object.fromEntries(map) as Record<K, V>;
}

export class InMemoryStorage implements ClientAgentSessionStorage {

  async dump() {
    return {
      database: 'memory',
      clientSessions: mapToObject( clientSessions ),
      profileCache: mapToObject( profileCache )
    }
  }

  //
  // Client sessions - agents are contacting me as a service.  I give them
  // challenges and then accept their authTokens
  //

  async createClientAgentSession( challenge: string ) {
    const id = nextSessionId++;
    clientSessions.set( id, { id, challenge, created: new Date() } as ClientAgentSession );
    return id;
  }

  async fetchClientAgentSession( id:number ) {
    return clientSessions.get( id );  
  }

  async updateClientAgentSession( id:number, updates:ClientAgentSessionUpdates ) {
    const session = clientSessions.get( id );
    if( !session )
      throw new Error("Failed to find client session by id: " + id );
    else
      clientSessions.set( id, { ...session, ...updates } );
  }


  //
  // Agentic Profile Cache
  //

  async cacheAgenticProfile( profile: AgenticProfile ) { 
    profileCache.set( profile.id, profile )
  }

  async getCachedAgenticProfile( did: DID ) {
    return profileCache.get( did )
  }
}
