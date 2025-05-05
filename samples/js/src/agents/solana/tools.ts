import { ai, z } from "./genkit.js";
import { Solana } from "@quicknode/sdk";
import { PublicKey } from "@solana/web3.js";

const solana = new Solana({
  endpointUrl: process.env.SOLANA_RPC_URL!,
});

// --- Get Slot Tool ---
export const getSlot = ai.defineTool(
  {
    name: "get_slot",
    description: "Get the current slot number from Solana",
    inputSchema: z.object({}), // No input required
  },
  async () => {
    console.log("[solana:getSlot]");
    try {
      const slot = await solana.connection.getSlot();
      return { slot };
    } catch (error) {
      console.error("Error getting slot:", error);
      throw error;
    }
  }
);

// --- Get Balance Tool ---
export const getBalance = ai.defineTool(
  {
    name: "get_balance",
    description: "Get SOL balance of a public key",
    inputSchema: z.object({
      publicKey: z.string().describe("The Solana wallet public key"),
    }),
  },
  async ({ publicKey }) => {
    console.log("[solana:getBalance]", publicKey);
    try {
      const lamports = await solana.connection.getBalance(
        new PublicKey(publicKey)
      );
      const sol = lamports / 1e9;
      return { balance: sol, unit: "SOL" };
    } catch (error) {
      console.error("Error getting balance:", error);
      throw error;
    }
  }
);
