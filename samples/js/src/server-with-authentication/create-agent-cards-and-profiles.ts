/**
 * Create agent cards and agentic profiles for demonstration and testing.  Also creates
 * an agentic profile for the user at ~/.agentic/iam/global-me/did.json along with a keyring.json
 * 
 * The "global-me" agentic profile is also published to the https://testing.agenticprofile.ai test service for global
 * availability.
 * 
 * This is usually run from the command line as "npm run a2a:setup-auth"
 */

import 'dotenv/config';

import os from "os";
import { join } from "path";
import { createEdDsaJwk, postJson } from "@agentic-profile/auth";
import {
  createAgenticProfile,
  prettyJson,
  webDidToUrl
} from "@agentic-profile/common";
import {
  __dirname,
  AGENT_CARD_TEMPLATE,
  saveAgentCard,
  saveProfile
} from "./misc.js";

const port = process.env.PORT || 41241;

(async ()=>{
  const keyring = [];
  const wwwDir = join( __dirname, "www" );

  try {
    // Well-known agentic profile and agent card for agent with no authentication
    let newKeys = await createAgentCardAndProfile({
      dir: join( wwwDir, ".well-known" ),
      did: `did:web:localhost:${port}`,
      services: [
        {
          name: "Well-known A2A coder with no authentication",
          type: "A2A",
          id: "a2a-coder",
          url: `http://localhost:${port}`
        }
      ],
      agent: {
        name: "Well-known A2A coder with no authentication",
        url: `http://localhost:${port}/agents/coder/`
      }
    });
    keyring.push( ...newKeys );

    // Coder agent with no authentication
    newKeys = await createAgentCardAndProfile({
      dir: join( wwwDir, "agents", "coder" ),
      did: `did:web:localhost:${port}:agents:coder`,
      services: [
        {
          name: "Named A2A coder with no authentication",
          type: "A2A",
          id: "a2a-coder",
          url: `http://localhost:${port}/agents/coder/`
        }
      ],
      agent: {
        name: "Named A2A coder with no authentication",
        url: `http://localhost:${port}/agents/coder/`
      }
    });
    keyring.push( ...newKeys );

    // Coder agent with authentication
    newKeys = await createAgentCardAndProfile({
      dir: join( wwwDir, "users", "2", "coder" ),
      did: `did:web:localhost:${port}:users:2:coder`,
      services: [
        {
          name: "A2A coder with authentication",
          type: "A2A",
          id: "a2a-coder",
          url: `http://localhost:${port}/users/2/coder/`
        }
      ],
      agent: {
        name: "A2A coder with authentication",
        url: `http://localhost:${port}/users/2/coder/`
      }
    });
    keyring.push( ...newKeys );

    newKeys = await createUserAgenticProfile();
    keyring.push( ...newKeys );

    //
    // Save combined keyring
    //
    await saveProfile({
      dir: __dirname, //join( __dirname, ".." ),
      keyring
    });

  } catch(error) {
    console.log( "Failed to save profile", error );
  }
})();

async function createUserAgenticProfile() {
  const services = [
    {
      name: "A2A coder client",
      type: "A2A",
      id: "a2a-client",
      url: `http://localhost:${port}/users/6/a2a-client`
    }
  ];
  const { profile, keyring, b64uPublicKey } = await createAgenticProfile({ services, createJwk: createEdDsaJwk });

  // publish to web:
  console.log( "Uploading agentic profile to https://testing.agenticprofile.ai..." );
  const { data } = await postJson(
    "https://testing.agenticprofile.ai/agentic-profile",
    { profile, b64uPublicKey }
  );
  const savedProfile = data.profile;

  // save locally.  Can be used by CLI with -i <profile> parameter
  const dir = join( os.homedir(), ".agentic", "iam", "global-me" );
  await saveProfile({ dir, profile: savedProfile, keyring });

  console.log(`Saved agentic profile to ${dir}

Shhhh! Keyring for testing... ${prettyJson( keyring )}`);

  return keyring;
}

async function createAgentCardAndProfile({ dir, did, services, agent }) {
  const { profile, keyring } = await createAgenticProfile({
    services,
    createJwk: createEdDsaJwk 
  });
  profile.id = did;

  const card = {
    ...AGENT_CARD_TEMPLATE,
    ...agent
  };

  await saveProfile({ dir, profile });
  console.log( `Saved profile to ${dir}/did.json
  DID: ${did}
  url: ${webDidToUrl(did)}` );
  await saveAgentCard( dir, card );
  console.log( `Saved agent card to ${dir}/agent.json\n` );

  return keyring;
}