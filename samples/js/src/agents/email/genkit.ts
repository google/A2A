import { genkit } from "genkit/beta";
import { defineEmailFormat } from "./email-format.js";
import { gemini15Flash, googleAI } from "@genkit-ai/googleai";

// Using a smaller/cheaper model as suggested by the reviewer
export const ai = genkit({
  plugins: [googleAI()],
  model: gemini15Flash, // Using the base model without specifying the more expensive version
});

defineEmailFormat(ai);

export { z } from "genkit/beta";