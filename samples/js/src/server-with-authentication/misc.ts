import {
  AgenticProfile,
  JWKSet,
  prettyJson
} from "@agentic-profile/common";

import { join } from "path";
import os from "os";
import {
  access,
  mkdir,
  readFile,
  writeFile
} from "fs/promises";

import {
  prettyJson,
  removeFragmentId
} from "@agentic-profile/common";

import { fileURLToPath } from "url";
import { dirname } from "path";

const __filename = fileURLToPath(import.meta.url);
export const __dirname = dirname(__filename);


type SaveProfileParams = {
  dir: string,
  profile?: AgenticProfile,
  keyring?: JWKSet[]
}

export async function saveProfile({ dir, profile, keyring }: SaveProfileParams) {
  await mkdir(dir, { recursive: true });

  const profilePath = join(dir, "did.json");
  if( profile ) {
    await writeFile(
      profilePath,
      prettyJson( profile ),
      "utf8"
    );
  }

  const keyringPath = join(dir, "keyring.json");
  if( keyring ) {
    await writeFile(
      keyringPath,
      prettyJson( keyring ),
      "utf8"
    );
  }  

  return { profilePath, keyringPath }
}

export async function loadProfileAndKeyring( dir: string ) {
  const profile = await loadProfile( dir );
  const keyring = await loadKeyring( dir );
  return { profile, keyring };
}

export async function hasProfile( dir: string ) {
  return await fileExists( join( dir, "did.json" ) );
}

export async function loadProfile( dir: string ) {
  return loadJson<AgenticProfile>( dir, "did.json" );
}

export async function loadKeyring( dir: string ) {
  return loadJson<JWKSet[]>( dir, "keyring.json" );
}

export async function loadJson<T>( dir: string, filename: string ): Promise<T> {
  const path = join( dir, filename );
  if( await fileExists( path ) !== true )
    throw new Error(`Failed to load ${path} - file not found`);

  const buffer = await readFile( path, "utf-8" );
  return JSON.parse( buffer ) as T;
}

export async function saveAgentCard( dir: string, card: AgentCard ) {
  await mkdir(dir, { recursive: true });
  await writeFile(
    join(dir, "agent.json"),
    prettyJson( card ),
    "utf8"
  );
}

export const AGENT_CARD_TEMPLATE = {
  "name": "Coder Agent",
  "description": "An agent that generates code based on natural language instructions and streams file outputs.",
  "url": null,
  "provider": {
    "organization": "A2A Samples"
  },
  "version": "0.0.1",
  "capabilities": {
    "streaming": true,
    "pushNotifications": false,
    "stateTransitionHistory": true
  },
  "authentication": null,
  "defaultInputModes": [
    "text"
  ],
  "defaultOutputModes": [
    "text",
    "file"
  ],
  "skills": [
    {
      "id": "code_generation",
      "name": "Code Generation",
      "description": "Generates code snippets or complete files based on user requests, streaming the results.",
      "tags": [
        "code",
        "development",
        "programming"
      ],
      "examples": [
        "Write a python function to calculate fibonacci numbers.",
        "Create an HTML file with a basic button that alerts 'Hello!' when clicked.",
        "Generate a TypeScript class for a user profile with name and email properties.",
        "Refactor this Java code to be more efficient.",
        "Write unit tests for the following Go function."
      ]
    }
  ]
};

export const AGENTIC_PROFILE_TEMPLATE = {
  "@context": [
    "https://www.w3.org/ns/did/v1",
    "https://w3id.org/security/suites/jws-2020/v1",
    "https://iamagentic.org/ns/agentic-profile/v1"
  ],
  "id": "did:web:localhost%3A3003",
  "verificationMethod": [
    {
      "id": "#identity-key",
      "type": "JsonWebKey2020",
      "publicKeyJwk": {
        "kty": "OKP",
        "alg": "EdDSA",
        "crv": "Ed25519",
        "x": "6EVHWPcPSJgxkTnjLWYLtjhHjIFWohzHnp9yelwJq6A"
      }
    }
  ],
  "service": [
    {
      "name": "Secure Coder",
      "id": "#a2a-coder",
      "type": "A2A",
      "serviceEndpoint": "http://localhost:3003/users/2/coder/",
      "capabilityInvocation": [
        {
          "id": "#agent-coder-key-0",
          "type": "JsonWebKey2020",
          "publicKeyJwk": {
            "kty": "OKP",
            "alg": "EdDSA",
            "crv": "Ed25519",
            "x": "ZESf0Wm6aAyYWFgttPywpDmlLhzTo7BNZXxq54ht0EE"
          }
        }
      ]
    }
  ]
};

//
// General util
//

async function fileExists(path: string): Promise<boolean> {
  try {
    await access(path);
    return true;
  } catch (error) {
    return false;
  }
}