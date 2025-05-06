import express from "express";
import cors, { CorsOptions } from "cors";

import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

interface AppOptions {
  corsOptions?: CorsOptions | boolean | string,
  wwwDir?: string[]
}

export function expressApp( { wwwDir, corsOptions }: AppOptions = {} ) {
  const app = express();

  /**
   * If a www directory is provided, then publish the files in that folder.
   */
  if( wwwDir ) {
    app.use("/", express.static(
        join(__dirname, ...wwwDir)
    ));
  }

  // Configure CORS
  if (corsOptions !== false) {
    const options =
    typeof corsOptions === "string"
      ? { origin: corsOptions }
      : corsOptions === true
      ? undefined // Use default cors options if true
      : corsOptions;
    app.use(cors(options));
  }

  app.use(express.json()); // Parse JSON bodies

  return app;
}