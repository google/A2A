import { genkit } from "genkit/beta";
import { defineCodeFormat } from "./code-format.js";
import { googleAI } from "@genkit-ai/googleai";

export const ai = genkit({
  plugins: [googleAI()],
  model: googleAI.model("gemini-2.5-pro-exp-03-25"),
});

defineCodeFormat(ai);

export { z } from "genkit/beta";
