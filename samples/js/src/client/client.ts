// Import necessary types from schema.ts
import {
  // Core types
  AgentCard,
  AgentCapabilities,
  JSONRPCRequest,
  JSONRPCResponse,
  JSONRPCError,
  // Task Request/Param types
  SendTaskRequest,
  GetTaskRequest,
  CancelTaskRequest,
  SendTaskStreamingRequest,
  TaskResubscriptionRequest,
  SetTaskPushNotificationRequest,
  GetTaskPushNotificationRequest,
  TaskSendParams,
  TaskQueryParams,
  TaskIdParams,
  TaskPushNotificationConfig,
  // Task Response/Result types
  SendTaskResponse,
  GetTaskResponse,
  CancelTaskResponse,
  SendTaskStreamingResponse,
  SetTaskPushNotificationResponse,
  GetTaskPushNotificationResponse,
  Task,
  // Task Streaming Payload types
  TaskStatusUpdateEvent,
  TaskArtifactUpdateEvent,
  // KG Request/Param types (NEW)
  KnowledgeQueryRequest,
  KnowledgeUpdateRequest,
  KnowledgeSubscribeRequest,
  KnowledgeQueryParams,
  KnowledgeUpdateParams,
  KnowledgeSubscribeParams,
  // KG Response/Result types (NEW)
  KnowledgeQueryResponse,
  KnowledgeUpdateResponse,
  KnowledgeQueryResponseResult,
  KnowledgeUpdateResponseResult,
  // KG Streaming Payload types (NEW)
  KnowledgeSubscriptionEvent,
  KnowledgeGraphChangeEvent,
} from "../schema.js";
// Import node:crypto for UUID generation if needed in browser fallback
import crypto from "node:crypto"; // Or use a browser-compatible UUID library

// Simple error class for client-side representation of JSON-RPC errors
class RpcError extends Error {
  code: number;
  data?: unknown;

  constructor(code: number, message: string, data?: unknown) {
    super(message);
    this.name = "RpcError";
    this.code = code;
    this.data = data;
  }
}

/**
 * A client implementation for the A2A protocol that communicates
 * with an A2A server over HTTP using JSON-RPC.
 */
export class A2AClient {
  private baseUrl: string;
  private fetchImpl: typeof fetch;
  private cachedAgentCard: AgentCard | null = null;

  /**
   * Creates an instance of A2AClient.
   * @param baseUrl The base URL of the A2A server endpoint.
   * @param fetchImpl Optional custom fetch implementation. Defaults to global fetch.
   */
  constructor(baseUrl: string, fetchImpl: typeof fetch = fetch) {
    this.baseUrl = baseUrl.endsWith("/") ? baseUrl.slice(0, -1) : baseUrl;
    this.fetchImpl = fetchImpl;
  }

  private _generateRequestId(): string | number {
    if (
      typeof crypto !== "undefined" &&
      typeof crypto.randomUUID === "function"
    ) {
      return crypto.randomUUID();
    } else {
      return Date.now() + Math.random(); // Basic fallback
    }
  }

  private async _makeHttpRequest<P>( // Generic for Params
    method: string, // Method name as string
    params: P,
    acceptHeader: "application/json" | "text/event-stream" = "application/json"
  ): Promise<Response> {
    const requestId = this._generateRequestId();
    const requestBody: JSONRPCRequest = {
      jsonrpc: "2.0",
      id: requestId,
      method: method,
      params: params as any, // Cast params, specific request types not needed here
    };

    try {
      const response = await this.fetchImpl(this.baseUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: acceptHeader,
        },
        body: JSON.stringify(requestBody),
      });
      return response;
    } catch (networkError) {
      console.error("Network error during RPC call:", networkError);
      throw new RpcError(
        -32603, // ErrorCodeInternalError
        `Network error: ${
          networkError instanceof Error
            ? networkError.message
            : String(networkError)
        }`,
        networkError
      );
    }
  }

  private async _handleJsonResponse<Res extends JSONRPCResponse>(
    response: Response,
    expectedMethod?: string
  ): Promise<Res["result"]> {
    let responseBody: string | null = null;
    try {
      responseBody = await response.text(); // Read body once

      if (!response.ok) {
        let errorData: JSONRPCError | null = null;
        try {
          const parsedError = JSON.parse(responseBody) as JSONRPCResponse;
          if (parsedError.error) {
            errorData = parsedError.error;
            throw new RpcError(
              errorData.code,
              errorData.message,
              errorData.data
            );
          }
        } catch (parseError) {
          // Fall through to generic HTTP error
        }
        throw new Error(
          `HTTP error ${response.status}: ${response.statusText}${
            responseBody ? ` - ${responseBody}` : ""
          }`
        );
      }

      const jsonResponse = JSON.parse(responseBody) as Res;

      if (
        typeof jsonResponse !== "object" ||
        jsonResponse === null ||
        jsonResponse.jsonrpc !== "2.0"
      ) {
        throw new RpcError(
          -32603, // ErrorCodeInternalError
          "Invalid JSON-RPC response structure received."
        );
      }

      if (jsonResponse.error) {
        throw new RpcError(
          jsonResponse.error.code,
          jsonResponse.error.message,
          jsonResponse.error.data
        );
      }

      return jsonResponse.result;
    } catch (error) {
      console.error(
        `Error processing RPC response for method ${
          expectedMethod || "unknown"
        }:`,
        error,
        responseBody ? `\nResponse Body: ${responseBody}` : ""
      );
      if (error instanceof RpcError) {
        throw error;
      } else {
        throw new RpcError(
          -32603, // ErrorCodeInternalError
          `Failed to process response: ${
            error instanceof Error ? error.message : String(error)
          }`,
          error
        );
      }
    }
  }

  private async *_handleStreamingResponse<StreamRes extends JSONRPCResponse>(
    response: Response,
    expectedMethod?: string
  ): AsyncIterable<StreamRes["result"]> {
    if (!response.ok || !response.body) {
      let errorText: string | null = null;
      try {
        errorText = await response.text();
      } catch (_) {}
      console.error(
        `HTTP error ${response.status} for streaming method ${expectedMethod}.`,
        errorText ? `Response: ${errorText}` : ""
      );
      throw new Error(
        `HTTP error ${response.status}: ${response.statusText} - Failed to establish stream.`
      );
    }

    const reader = response.body
      .pipeThrough(new TextDecoderStream())
      .getReader();
    let buffer = "";

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += value;
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const message of lines) {
          if (message.startsWith("data: ")) {
            const dataLine = message.substring("data: ".length).trim();
            if (dataLine) {
              try {
                const parsedData = JSON.parse(dataLine) as StreamRes;
                if (
                  typeof parsedData !== "object" ||
                  parsedData === null ||
                  parsedData.jsonrpc !== "2.0"
                ) {
                  console.error(`Invalid SSE data structure:`, dataLine);
                  continue;
                }

                if (parsedData.error) {
                  console.error(`Error in SSE stream:`, parsedData.error);
                  throw new RpcError(
                    parsedData.error.code,
                    parsedData.error.message,
                    parsedData.error.data
                  ); // Terminate stream on error
                } else if (parsedData.result !== undefined) {
                  yield parsedData.result as StreamRes["result"];
                } else {
                  console.warn(`SSE data has neither result nor error:`, parsedData);
                }
              } catch (e) {
                console.error(`Failed to parse SSE data line:`, dataLine, e);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error(`Error reading SSE stream for ${expectedMethod}:`, error);
      throw error; // Re-throw
    } finally {
      reader.releaseLock();
      console.log(`SSE stream finished for ${expectedMethod}.`);
    }
  }

  /** Fetches the agent card, caching the result. */
  async agentCard(): Promise<AgentCard> {
    if (this.cachedAgentCard) {
      return this.cachedAgentCard;
    }
    // Fetch from standard .well-known path
    const cardUrl = new URL("/.well-known/agent.json", this.baseUrl).toString();
    try {
      const response = await this.fetchImpl(cardUrl, {
        method: "GET",
        headers: { Accept: "application/json" },
      });
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      const card = await response.json();
      // TODO: Add schema validation for the card
      this.cachedAgentCard = card as AgentCard;
      return this.cachedAgentCard;
    } catch (error) {
      console.error(`Failed to fetch/parse agent card from ${cardUrl}:`, error);
      throw new RpcError(
        -32603, // ErrorCodeInternalError
        `Could not retrieve agent card: ${
          error instanceof Error ? error.message : String(error)
        }`,
        error
      );
    }
  }

  /** Sends a task request (non-streaming). */
  async sendTask(params: TaskSendParams): Promise<Task | null> {
    const httpResponse = await this._makeHttpRequest<TaskSendParams>(
      "tasks/send",
      params
    );
    return this._handleJsonResponse<SendTaskResponse>(
      httpResponse,
      "tasks/send"
    );
  }

  /** Sends a task and subscribes to streaming updates. */
  sendTaskSubscribe(
    params: TaskSendParams
  ): AsyncIterable<TaskStatusUpdateEvent | TaskArtifactUpdateEvent> {
    const streamGenerator = async function* (
      this: A2AClient
    ): AsyncIterable<TaskStatusUpdateEvent | TaskArtifactUpdateEvent> {
      // Check capability
      if (!(await this.supports("streaming"))) {
         throw new RpcError(-32601, "Agent does not support streaming (tasks/sendSubscribe).");
      }
      const httpResponse = await this._makeHttpRequest<TaskSendParams>(
        "tasks/sendSubscribe",
        params,
        "text/event-stream"
      );
      yield* this._handleStreamingResponse<SendTaskStreamingResponse>(
        httpResponse,
        "tasks/sendSubscribe"
      );
    }.bind(this)();
    return streamGenerator;
  }

  /** Retrieves the current state of a task. */
  async getTask(params: TaskQueryParams): Promise<Task | null> {
    const httpResponse = await this._makeHttpRequest<TaskQueryParams>(
      "tasks/get",
      params
    );
    return this._handleJsonResponse<GetTaskResponse>(httpResponse, "tasks/get");
  }

  /** Cancels a currently running task. */
  async cancelTask(params: TaskIdParams): Promise<Task | null> {
    const httpResponse = await this._makeHttpRequest<TaskIdParams>(
      "tasks/cancel",
      params
    );
    return this._handleJsonResponse<CancelTaskResponse>(
      httpResponse,
      "tasks/cancel"
    );
  }

  /** Sets or updates the push notification config for a task. */
  async setTaskPushNotification(
    params: TaskPushNotificationConfig
  ): Promise<TaskPushNotificationConfig | null> {
    // Check capability
    if (!(await this.supports("pushNotifications"))) {
       throw new RpcError(-32601, "Agent does not support push notifications (tasks/pushNotification/set).");
    }
    const httpResponse = await this._makeHttpRequest<TaskPushNotificationConfig>(
      "tasks/pushNotification/set",
      params
    );
    return this._handleJsonResponse<SetTaskPushNotificationResponse>(
      httpResponse,
      "tasks/pushNotification/set"
    );
  }

  /** Retrieves the push notification config for a task. */
  async getTaskPushNotification(
    params: TaskIdParams
  ): Promise<TaskPushNotificationConfig | null> {
     // Check capability
     if (!(await this.supports("pushNotifications"))) {
       throw new RpcError(-32601, "Agent does not support push notifications (tasks/pushNotification/get).");
    }
    const httpResponse = await this._makeHttpRequest<TaskIdParams>(
      "tasks/pushNotification/get",
      params
    );
    return this._handleJsonResponse<GetTaskPushNotificationResponse>(
      httpResponse,
      "tasks/pushNotification/get"
    );
  }

  /** Resubscribes to updates for a task. */
  resubscribeTask(
    params: TaskQueryParams // Use TaskQueryParams for potential history length
  ): AsyncIterable<TaskStatusUpdateEvent | TaskArtifactUpdateEvent> {
    const streamGenerator = async function* (
      this: A2AClient
    ): AsyncIterable<TaskStatusUpdateEvent | TaskArtifactUpdateEvent> {
       // Check capability
      if (!(await this.supports("streaming"))) {
         throw new RpcError(-32601, "Agent does not support streaming (tasks/resubscribe).");
      }
      const httpResponse = await this._makeHttpRequest<TaskQueryParams>(
        "tasks/resubscribe",
        params,
        "text/event-stream"
      );
      yield* this._handleStreamingResponse<SendTaskStreamingResponse>(
        httpResponse,
        "tasks/resubscribe"
      );
    }.bind(this)();
    return streamGenerator;
  }

  // --- NEW Knowledge Graph Methods ---

  /** Queries the agent's knowledge graph. */
  async knowledgeQuery(params: KnowledgeQueryParams): Promise<KnowledgeQueryResponseResult | null> {
     // Check capability
     if (!(await this.supports("knowledgeGraph"))) {
       throw new RpcError(-32601, "Agent does not support knowledge graph features (knowledge/query).");
     }
     // Optional: Check if 'graphql' is in knowledgeGraphQueryLanguages
     const card = await this.agentCard();
     if (!card.capabilities?.knowledgeGraphQueryLanguages?.includes("graphql")) {
         throw new RpcError(-32601, "Agent does not support GraphQL for knowledge queries.");
     }

    const httpResponse = await this._makeHttpRequest<KnowledgeQueryParams>(
      "knowledge/query",
      params
    );
    return this._handleJsonResponse<KnowledgeQueryResponse>(httpResponse, "knowledge/query");
  }

  /** Proposes updates to the agent's knowledge graph. */
  async knowledgeUpdate(params: KnowledgeUpdateParams): Promise<KnowledgeUpdateResponseResult | null> {
    // Check capability
     if (!(await this.supports("knowledgeGraph"))) {
       throw new RpcError(-32601, "Agent does not support knowledge graph features (knowledge/update).");
     }
    const httpResponse = await this._makeHttpRequest<KnowledgeUpdateParams>(
      "knowledge/update",
      params
    );
    return this._handleJsonResponse<KnowledgeUpdateResponse>(httpResponse, "knowledge/update");
  }

  /** Subscribes to changes in the agent's knowledge graph. */
  knowledgeSubscribe(
    params: KnowledgeSubscribeParams
  ): AsyncIterable<KnowledgeGraphChangeEvent> {
    const streamGenerator = async function* (
      this: A2AClient
    ): AsyncIterable<KnowledgeGraphChangeEvent> {
       // Check capabilities
      if (!(await this.supports("knowledgeGraph")) || !(await this.supports("streaming"))) {
         throw new RpcError(-32601, "Agent does not support streaming knowledge graph subscriptions.");
      }
      // Optional: Check if 'graphql' is in knowledgeGraphQueryLanguages
      const card = await this.agentCard();
      if (!card.capabilities?.knowledgeGraphQueryLanguages?.includes("graphql")) {
         throw new RpcError(-32601, "Agent does not support GraphQL for knowledge subscriptions.");
      }

      const httpResponse = await this._makeHttpRequest<KnowledgeSubscribeParams>(
        "knowledge/subscribe",
        params,
        "text/event-stream"
      );
      // The streaming handler yields the 'result' part of the event, which is KnowledgeGraphChangeEvent
      yield* this._handleStreamingResponse<KnowledgeSubscriptionEvent>(
        httpResponse,
        "knowledge/subscribe"
      );
    }.bind(this)();
    // Type assertion might be needed if TS cannot infer yield type perfectly
    return streamGenerator as AsyncIterable<KnowledgeGraphChangeEvent>;
  }

  /** Checks if the server likely supports specific capabilities based on agent card. */
  async supports(
      capability: "streaming" | "pushNotifications" | "knowledgeGraph"
  ): Promise<boolean> {
    try {
      const card = await this.agentCard();
      switch (capability) {
        case "streaming":
          return !!card.capabilities?.streaming;
        case "pushNotifications":
          return !!card.capabilities?.pushNotifications;
        case "knowledgeGraph":
          return !!card.capabilities?.knowledgeGraph;
        default:
          return false;
      }
    } catch (error) {
      console.error(`Failed to check support for capability '${capability}':`, error);
      return false;
    }
  }
}
