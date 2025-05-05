import { genkit, z, GenerationCommonConfigSchema } from "genkit";
import { openAI } from "genkitx-openai";
import { dirname } from "path";
import { fileURLToPath } from "url";

const qwenModelInfo = {
  label: "Qwen 2.5 Coder 32B Instruct",
  supports: {
    multiturn: true,
    tools: true,
    media: false,
    systemRole: true,
    output: ["text"],
  },
};

const qwenConfigSchema = GenerationCommonConfigSchema.extend({
  temperature: z.number().min(0).max(2).optional(),
  topP: z.number().min(0).max(1).optional(),
  maxTokens: z.number().int().optional(),
});

export const ai = genkit({
  plugins: [
    openAI({
      apiKey: process.env.HEURIST_API_KEY,
      baseURL: "https://llm-gateway.heurist.xyz/v1",
      models: [
        {
          name: "qwen/qwen-2.5-coder-32b-instruct",
          info: qwenModelInfo,
          configSchema: qwenConfigSchema,
        },
      ],
    }),
  ],
  model: "openai/qwen/qwen-2.5-coder-32b-instruct",
  promptDir: dirname(fileURLToPath(import.meta.url)),
});

export { z } from "genkit";
