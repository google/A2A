import express, {
  Request,
  Response,
  NextFunction,
  RequestHandler,
} from "express";
import cors, { CorsOptions } from "cors";
import * as schema from "../schema.js";
import { TaskStore, InMemoryTaskStore, TaskAndHistory } from "./store.js";
import { TaskHandler, TaskContext as OldTaskContext } from "./handler.js";
import { A2AError } from "./error.js";
import {
  getCurrentTimestamp,
  isTaskStatusUpdate,
  isArtifactUpdate,
} from "./utils.js";

/** Options for configuring the A2AServer. */
export interface A2AServerOptions {
  taskStore?: TaskStore;
  cors?: CorsOptions | boolean | string;
  basePath?: string;
  card?: schema.AgentCard; // Agent Card is now optional but recommended
  // Potential: Add KnowledgeStore if separating concerns
  // knowledgeStore?: KnowledgeStore;
}

/** Context passed to TaskHandler. */
export interface TaskContext extends Omit<OldTaskContext, "taskStore"> {}

/** Implements an A2A specification compliant server using Express. */
export class A2AServer {
  private taskHandler: TaskHandler;
  private taskStore: TaskStore;
  // Placeholder: Add knowledgeStore if implemented separately
  // private knowledgeStore: KnowledgeStore;
  private corsOptions: CorsOptions | boolean | string;
  private basePath: string;
  private activeCancellations: Set<string> = new Set();
  private card: schema.AgentCard; // Make card required internally after constructor check

  constructor(handler: TaskHandler, options: A2AServerOptions = {}) {
    this.taskHandler = handler;
    this.taskStore = options.taskStore ?? new InMemoryTaskStore();
    // If separating stores: this.knowledgeStore = options.knowledgeStore ?? this.taskStore as any;
    this.corsOptions = options.cors ?? true;
    this.basePath = options.basePath ?? "/";
    if (!options.card) {
      // Provide a default minimal card if none is given
      console.warn("No AgentCard provided to A2AServer, using minimal default.");
      this.card = {
        name: "Default A2A Agent",
        version: "0.0.0",
        url: `http://localhost:41241${this.basePath}`, // Placeholder URL
        capabilities: {
          // Default capabilities (minimal)
          streaming: false,
          pushNotifications: false,
          stateTransitionHistory: false,
          knowledgeGraph: false, // Default KG support to false
          knowledgeGraphQueryLanguages: [],
        },
        skills: [{ id: "default", name: "Default Handler" }],
      };
    } else {
      this.card = options.card;
    }

    if (this.basePath !== "/") {
      this.basePath = `/${this.basePath.replace(/^\/|\/$/g, "")}/`;
    }
  }

  start(port = 41241): express.Express {
    const app = express();
    if (this.corsOptions !== false) {
      const options =
        typeof this.corsOptions === "string"
          ? { origin: this.corsOptions }
          : this.corsOptions === true
          ? undefined
          : this.corsOptions;
      app.use(cors(options));
    }
    app.use(express.json());

    // Serve Agent Card at .well-known path
    app.get("/.well-known/agent.json", (req, res) => {
      res.json(this.card);
    });

    app.post(this.basePath, this.endpoint());
    app.use(this.errorHandler);

    app.listen(port, () => {
      console.log(
        `A2A Server (${this.card.name}) listening on port ${port} at path ${this.basePath}`
      );
      console.log(`Capabilities:`, this.card.capabilities);
    });

    return app;
  }

  endpoint(): RequestHandler {
    return async (req: Request, res: Response, next: NextFunction) => {
      const requestBody = req.body;
      let taskId: string | undefined;
      let reqId: number | string | null = null; // Capture request ID early

      try {
        if (!this.isValidJsonRpcRequest(requestBody)) {
          throw A2AError.invalidRequest("Invalid JSON-RPC request structure.");
        }
        reqId = requestBody.id ?? null; // Get ID after basic validation

        // Attempt to get task ID early for error context.
        taskId = (requestBody.params as any)?.id;

        // Route based on method & check capabilities
        switch (requestBody.method) {
          // --- Task Methods ---
          case "tasks/send":
            await this.handleTaskSend(
              requestBody as schema.SendTaskRequest,
              res
            );
            break;
          case "tasks/sendSubscribe":
            if (!this.card.capabilities.streaming) {
              throw A2AError.methodNotFound(requestBody.method);
            }
            await this.handleTaskSendSubscribe(
              requestBody as schema.SendTaskStreamingRequest,
              res
            );
            break;
          case "tasks/get":
            await this.handleTaskGet(requestBody as schema.GetTaskRequest, res);
            break;
          case "tasks/cancel":
            await this.handleTaskCancel(
              requestBody as schema.CancelTaskRequest,
              res
            );
            break;
          case "tasks/pushNotification/set":
            if (!this.card.capabilities.pushNotifications) {
              throw A2AError.methodNotFound(requestBody.method);
            }
            await this.handleSetTaskPushNotification(
              requestBody as schema.SetTaskPushNotificationRequest,
              res
            );
            break;
          case "tasks/pushNotification/get":
            if (!this.card.capabilities.pushNotifications) {
              throw A2AError.methodNotFound(requestBody.method);
            }
            await this.handleGetTaskPushNotification(
              requestBody as schema.GetTaskPushNotificationRequest,
              res
            );
            break;
           case "tasks/resubscribe":
            if (!this.card.capabilities.streaming) {
              throw A2AError.methodNotFound(requestBody.method);
            }
            await this.handleTaskResubscribe(
              requestBody as schema.TaskResubscriptionRequest,
              res
            );
            break;

          // --- Knowledge Methods ---
          case "knowledge/query":
            if (!this.card.capabilities.knowledgeGraph) {
              throw A2AError.methodNotFound(requestBody.method);
            }
            await this.handleKnowledgeQuery(
              requestBody as schema.KnowledgeQueryRequest,
              res
            );
            break;
          case "knowledge/update":
            if (!this.card.capabilities.knowledgeGraph) {
              throw A2AError.methodNotFound(requestBody.method);
            }
            await this.handleKnowledgeUpdate(
              requestBody as schema.KnowledgeUpdateRequest,
              res
            );
            break;
          case "knowledge/subscribe":
            if (
              !this.card.capabilities.knowledgeGraph ||
              !this.card.capabilities.streaming
            ) {
              throw A2AError.methodNotFound(requestBody.method);
            }
            await this.handleKnowledgeSubscribe(
              requestBody as schema.KnowledgeSubscribeRequest,
              res
            );
            break;

          default:
            throw A2AError.methodNotFound(requestBody.method);
        }
      } catch (error) {
        // Add captured request ID to error context
        next(this.normalizeError(error, reqId, taskId));
      }
    };
  }

  // --- Request Handlers ---

  // (handleTaskSend, handleTaskSendSubscribe, handleTaskGet, handleTaskCancel remain largely the same,
  //  but ensure they use the updated TaskAndHistory and TaskContext from store.ts/server.ts)

    // --- Request Handlers ---

  private async handleTaskSend(
    req: schema.SendTaskRequest,
    res: Response
  ): Promise<void> {
    this.validateTaskSendParams(req.params);
    const { id: taskId, message, sessionId, metadata } = req.params;

    let currentData = await this.loadOrCreateTaskAndHistory(taskId, message, sessionId, metadata);
    const context = this.createTaskContext(currentData.task, message, currentData.history);
    const generator = this.taskHandler(context);

    try {
      for await (const yieldValue of generator) {
        currentData = this.applyUpdateToTaskAndHistory(currentData, yieldValue);
        await this.taskStore.save(currentData);
        context.task = currentData.task; // Update context for handler
      }
      // If generator returns a Task, use it as the final state
      // Note: Pydantic returns the value, TS requires explicit check if handler can return non-void
      // Assuming handler might return void or Task | void based on original python
      // Let's assume for non-streaming, we expect the final task state back from the handler or store
      const finalTaskFromHandler = await generator.return(); // Check return value
      if (finalTaskFromHandler && typeof finalTaskFromHandler === 'object' && 'id' in finalTaskFromHandler) {
          // If handler returned a task, ensure it's saved (though yields should have saved intermediate states)
          console.log(`[Task ${taskId}] Handler returned final task object.`);
          // Optionally re-apply just to be safe and get history alignment
          currentData = this.applyUpdateToTaskAndHistory(currentData, finalTaskFromHandler.status);
          if(finalTaskFromHandler.artifacts) {
              currentData.task.artifacts = finalTaskFromHandler.artifacts;
          }
          await this.taskStore.save(currentData);
      } else {
         console.log(`[Task ${taskId}] Handler finished (void return). Using last yielded state.`);
         // Reload from store to be absolutely sure we have the final state after all yields
         const finalData = await this.taskStore.load(taskId);
         if(finalData) currentData = finalData;
      }

    } catch (handlerError) {
      // Error handling: Set state to failed, save, and rethrow
      const failureStatusUpdate: Omit<schema.TaskStatus, "timestamp"> = {
        state: "failed",
        message: { role: "agent", parts: [{ text: `Handler failed: ${handlerError instanceof Error ? handlerError.message : String(handlerError)}` }] },
      };
      currentData = this.applyUpdateToTaskAndHistory(currentData, failureStatusUpdate);
      try { await this.taskStore.save(currentData); } catch (saveError) { console.error(`Failed to save task ${taskId} after handler error:`, saveError); }
      throw this.normalizeError(handlerError, req.id, taskId);
    }

    this.sendJsonResponse(res, req.id, currentData.task);
  }

  private async handleTaskSendSubscribe(
    req: schema.SendTaskStreamingRequest,
    res: Response
  ): Promise<void> {
    this.validateTaskSendParams(req.params);
    const { id: taskId, message, sessionId, metadata } = req.params;

    let currentData = await this.loadOrCreateTaskAndHistory(taskId, message, sessionId, metadata);
    const context = this.createTaskContext(currentData.task, message, currentData.history);
    const generator = this.taskHandler(context);

    res.writeHead(200, {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    });
    const sendEvent = (eventData: schema.JSONRPCResponse) => {
      res.write(`data: ${JSON.stringify(eventData)}\n\n`);
    };

    let lastEventWasFinal = false;

    try {
      // Optional initial state event:
      // sendEvent(this.createSuccessResponse(req.id, this.createTaskStatusEvent(taskId, currentData.task.status, false)));

      for await (const yieldValue of generator) {
        currentData = this.applyUpdateToTaskAndHistory(currentData, yieldValue);
        await this.taskStore.save(currentData);
        context.task = currentData.task; // Update context

        let event: schema.TaskStatusUpdateEvent | schema.TaskArtifactUpdateEvent;
        let isFinal = false;

        if (isTaskStatusUpdate(yieldValue)) {
          const terminalStates: schema.TaskState[] = ["completed", "failed", "canceled"];
          isFinal = terminalStates.includes(currentData.task.status.state);
          event = this.createTaskStatusEvent(taskId, currentData.task.status, isFinal);
        } else if (isArtifactUpdate(yieldValue)) {
            // Find the updated artifact (potentially appended/merged)
            const updatedArtifact = currentData.task.artifacts?.find(a =>
                (a.index !== undefined && a.index === yieldValue.index) ||
                (a.name && a.name === yieldValue.name)
            ) ?? yieldValue; // Fallback to the yielded value if not found (shouldn't happen often)
           event = this.createTaskArtifactEvent(taskId, updatedArtifact);
        } else {
          console.warn("[SSE] Handler yielded unknown value:", yieldValue);
          continue;
        }

        sendEvent(this.createSuccessResponse(req.id, event));
        lastEventWasFinal = isFinal;
        if (isFinal) break;
      }

      // Loop finished. Check if a final event was already sent.
       if (!lastEventWasFinal) {
        const finalStates: schema.TaskState[] = ["completed", "failed", "canceled"];
        if (!finalStates.includes(currentData.task.status.state)) {
            console.warn(`[SSE ${taskId}] Handler finished non-terminally (${currentData.task.status.state}). Forcing 'completed'.`);
            currentData = this.applyUpdateToTaskAndHistory(currentData, { state: "completed" });
            await this.taskStore.save(currentData);
        }
        const finalEvent = this.createTaskStatusEvent(taskId, currentData.task.status, true);
        sendEvent(this.createSuccessResponse(req.id, finalEvent));
      }

    } catch (handlerError) {
      console.error(`[SSE ${taskId}] Handler error during streaming:`, handlerError);
      const failureUpdate: Omit<schema.TaskStatus, "timestamp"> = {
        state: "failed",
        message: { role: "agent", parts: [{ text: `Handler failed: ${handlerError instanceof Error ? handlerError.message : String(handlerError)}` }] },
      };
      currentData = this.applyUpdateToTaskAndHistory(currentData, failureUpdate);
      try { await this.taskStore.save(currentData); } catch (saveError) { console.error(`[SSE ${taskId}] Failed to save task after handler error:`, saveError); }

      const errorEvent = this.createTaskStatusEvent(taskId, currentData.task.status, true);
      sendEvent(this.createSuccessResponse(req.id, errorEvent));
    } finally {
      if (!res.writableEnded) {
        res.end();
      }
    }
  }

  private async handleTaskGet(req: schema.GetTaskRequest, res: Response): Promise<void> {
    this.validateTaskIdParams(req.params); // Use base validation
    const { id: taskId, historyLength } = req.params;
    const data = await this.taskStore.load(taskId);
    if (!data) {
      throw A2AError.taskNotFound(taskId);
    }
    // Handle history length parameter if needed (schema allows TaskQueryParams)
    const taskToSend = this.applyHistoryLength(data.task, historyLength);
    this.sendJsonResponse(res, req.id, taskToSend);
  }

  private async handleTaskCancel(req: schema.CancelTaskRequest, res: Response): Promise<void> {
    this.validateTaskIdParams(req.params);
    const { id: taskId } = req.params;
    let data = await this.taskStore.load(taskId);
    if (!data) {
      throw A2AError.taskNotFound(taskId);
    }

    const finalStates: schema.TaskState[] = ["completed", "failed", "canceled"];
    if (finalStates.includes(data.task.status.state)) {
      console.log(`Task ${taskId} already final (${data.task.status.state}), cannot cancel.`);
      this.sendJsonResponse(res, req.id, data.task);
      return;
    }

    this.activeCancellations.add(taskId);
    const cancelUpdate: Omit<schema.TaskStatus, "timestamp"> = {
      state: "canceled",
      message: { role: "agent", parts: [{ text: "Task cancelled by request." }] },
    };
    data = this.applyUpdateToTaskAndHistory(data, cancelUpdate);
    await this.taskStore.save(data);
    this.activeCancellations.delete(taskId);
    this.sendJsonResponse(res, req.id, data.task);
  }

   private async handleSetTaskPushNotification(req: schema.SetTaskPushNotificationRequest, res: Response): Promise<void> {
     this.validateTaskPushNotificationConfig(req.params);
     const { id: taskId, pushNotificationConfig } = req.params;

     // Check if task exists before setting config
     const existingTask = await this.taskStore.load(taskId);
     if (!existingTask) {
       throw A2AError.taskNotFound(taskId);
     }

     // TODO: Implement saving push config (likely separate from TaskStore or as task metadata)
     console.warn(`[Server] Push notification config saving for task ${taskId} is not fully implemented. Storing in memory only for now.`);
     // Placeholder: store it in memory associated with the task store instance
     (this.taskStore as any)._pushConfigs = (this.taskStore as any)._pushConfigs || {};
     (this.taskStore as any)._pushConfigs[taskId] = pushNotificationConfig;


     // Return the request params as confirmation
     this.sendJsonResponse(res, req.id, req.params);
   }

   private async handleGetTaskPushNotification(req: schema.GetTaskPushNotificationRequest, res: Response): Promise<void> {
       this.validateTaskIdParams(req.params);
       const { id: taskId } = req.params;

       // Check if task exists
       const existingTask = await this.taskStore.load(taskId);
       if (!existingTask) {
           throw A2AError.taskNotFound(taskId);
       }

       // TODO: Implement loading push config
       console.warn(`[Server] Push notification config loading for task ${taskId} is not fully implemented. Checking in-memory only.`);
       const pushConfig = (this.taskStore as any)._pushConfigs?.[taskId];

       if (!pushConfig) {
            // Option 1: Return null result (client handles "not set")
            this.sendJsonResponse(res, req.id, null);
            // Option 2: Throw a specific error (e.g., custom or use PushNotificationNotSupported)
            // throw new A2AError(schema.ErrorCodePushNotificationNotSupported, `Push notification config not set for task ${taskId}`);
           return;
       }

       const result: schema.TaskPushNotificationConfig = { id: taskId, pushNotificationConfig: pushConfig };
       this.sendJsonResponse(res, req.id, result);
   }

   private async handleTaskResubscribe(req: schema.TaskResubscriptionRequest, res: Response): Promise<void> {
        // Validation: Use TaskQueryParams validation
        this.validateTaskQueryParams(req.params);
        const { id: taskId, historyLength } = req.params; // historyLength might be used later

        // Check if task exists
        const currentData = await this.taskStore.load(taskId);
        if (!currentData) {
            throw A2AError.taskNotFound(taskId);
        }

        // Check if task is already in a final state
        const finalStates: schema.TaskState[] = ["completed", "failed", "canceled"];
        if (finalStates.includes(currentData.task.status.state)) {
            console.log(`[Resubscribe ${taskId}] Task already final (${currentData.task.status.state}). Sending final status event.`);
            res.writeHead(200, {
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                Connection: "keep-alive",
            });
            const finalEvent = this.createTaskStatusEvent(taskId, currentData.task.status, true);
            const finalResponse = this.createSuccessResponse(req.id, finalEvent);
            res.write(`data: ${JSON.stringify(finalResponse)}\n\n`);
            res.end();
            return;
        }

        // TODO: Implement actual resubscription logic.
        // This requires tracking active SSE connections per task and potentially
        // replaying missed events or just sending the current state and future updates.
        // For now, just acknowledge and send an error indicating not implemented.
        console.error(`[Resubscribe ${taskId}] Resubscription logic not implemented.`);
        throw A2AError.unsupportedOperation("tasks/resubscribe - Resubscription logic pending implementation.");

        // --- Ideal Future Logic ---
        // 1. Add connection to list of subscribers for taskId
        // 2. Optionally send current task state/recent history
        // 3. Stream subsequent updates via SSE as they happen
        // (Similar to sendSubscribe but joining mid-stream)
   }

  // --- NEW Knowledge Method Handlers (STUBS) ---

  private async handleKnowledgeQuery(req: schema.KnowledgeQueryRequest, res: Response): Promise<void> {
    console.warn(`[Server] Received knowledge/query for task ${req.params.taskId}, but KG features are not implemented.`);
    // In a real implementation: validate params, check capabilities/permissions,
    // execute query via KnowledgeStore/Manager, format response.
    throw A2AError.unsupportedOperation("knowledge/query");
  }

  private async handleKnowledgeUpdate(req: schema.KnowledgeUpdateRequest, res: Response): Promise<void> {
     console.warn(`[Server] Received knowledge/update for task ${req.params.taskId}, but KG features are not implemented.`);
     // In a real implementation: validate params, check capabilities/permissions,
     // perform alignment verification, apply patches via KnowledgeStore/Manager, format response.
     throw A2AError.unsupportedOperation("knowledge/update");
  }

   private async handleKnowledgeSubscribe(req: schema.KnowledgeSubscribeRequest, res: Response): Promise<void> {
      console.warn(`[Server] Received knowledge/subscribe for task ${req.params.taskId}, but KG features are not implemented.`);
      // In a real implementation: validate params, check capabilities/permissions,
      // setup subscription stream via KnowledgeStore/Manager, manage SSE connection.
      throw A2AError.unsupportedOperation("knowledge/subscribe");
   }


  // --- Helper & Validation Methods ---

   private applyHistoryLength(task: schema.Task, historyLength?: number | null): schema.Task {
       if (historyLength === null || historyLength === undefined || historyLength <= 0) {
           // Return task without history if length is null, undefined or 0
           const { history, ...taskWithoutHistory } = task;
           return taskWithoutHistory;
       }
       if (task.history && task.history.length > historyLength) {
           // Return task with truncated history
           return {
               ...task,
               history: task.history.slice(-historyLength)
           };
       }
       // Return task as is (history is absent or already short enough)
       return task;
   }

  private applyUpdateToTaskAndHistory(
    current: TaskAndHistory,
    update: Omit<schema.TaskStatus, "timestamp"> | schema.Artifact
  ): TaskAndHistory {
    let newTask = { ...current.task };
    let newHistory = [...current.history];

    if (isTaskStatusUpdate(update)) {
      newTask.status = { ...newTask.status, ...update, timestamp: getCurrentTimestamp() };
      if (update.message?.role === "agent") {
        newHistory.push(update.message);
      }
    } else if (isArtifactUpdate(update)) {
      newTask.artifacts = [...(newTask.artifacts || [])]; // Ensure array exists and is a copy
      const existingIndex = update.index ?? -1;
      let replaced = false;

      if (existingIndex >= 0 && existingIndex < newTask.artifacts.length) {
          // Handle append or replace logic at index
          if (update.append) {
              const appendedArtifact = JSON.parse(JSON.stringify(newTask.artifacts[existingIndex])); // Deep copy needed
              appendedArtifact.parts.push(...update.parts);
              // Merge metadata, update other fields if provided
              if(update.metadata) appendedArtifact.metadata = {...(appendedArtifact.metadata || {}), ...update.metadata};
              if(update.description) appendedArtifact.description = update.description;
              if(update.lastChunk !== undefined) appendedArtifact.lastChunk = update.lastChunk;
              newTask.artifacts[existingIndex] = appendedArtifact;
          } else {
              newTask.artifacts[existingIndex] = { ...update }; // Overwrite with copy
          }
          replaced = true;
      } else if (update.name) {
          // Handle replace by name
          const namedIndex = newTask.artifacts.findIndex(a => a.name === update.name);
          if (namedIndex >= 0) {
              newTask.artifacts[namedIndex] = { ...update }; // Replace with copy
              replaced = true;
          }
      }
      if (!replaced) {
          newTask.artifacts.push({ ...update }); // Add new artifact (copy)
          // Sort if indices are used
          if (newTask.artifacts.some(a => a.index !== undefined && a.index >= 0)) {
             newTask.artifacts.sort((a, b) => (a.index ?? Infinity) - (b.index ?? Infinity));
          }
      }
    }
    return { task: newTask, history: newHistory };
  }

  private async loadOrCreateTaskAndHistory(
    taskId: string,
    initialMessage: schema.Message,
    sessionId?: string | null,
    metadata?: Record<string, unknown> | null
  ): Promise<TaskAndHistory> {
    let data = await this.taskStore.load(taskId);
    let needsSave = false;

    if (!data) {
      const initialTask: schema.Task = {
        id: taskId,
        sessionId: sessionId ?? undefined,
        status: { state: "submitted", timestamp: getCurrentTimestamp(), message: null },
        artifacts: [],
        history: [], // Initialize history here for consistency
        metadata: metadata ?? undefined,
      };
      const initialHistory: schema.Message[] = [initialMessage];
      data = { task: initialTask, history: initialHistory };
      needsSave = true;
      console.log(`[Task ${taskId}] Created new task.`);
    } else {
      console.log(`[Task ${taskId}] Loaded existing task.`);
      data = { task: data.task, history: [...data.history, initialMessage] };
      needsSave = true; // Always save on new message

      // State transition logic
      const finalStates: schema.TaskState[] = ["completed", "failed", "canceled"];
      if (finalStates.includes(data.task.status.state)) {
         console.warn(`[Task ${taskId}] Received message for final task. Resetting to 'submitted'.`);
         data = this.applyUpdateToTaskAndHistory(data, { state: "submitted", message: null });
      } else if (data.task.status.state === "input-required") {
         console.log(`[Task ${taskId}] Input received. Setting state to 'working'.`);
         data = this.applyUpdateToTaskAndHistory(data, { state: "working" });
      }
      // If 'submitted' or 'working', just appending history is usually fine.
    }

    if (needsSave) {
      await this.taskStore.save(data);
    }
    // Return copies
    return { task: { ...data.task }, history: [...data.history] };
  }

  private createTaskContext(
    task: schema.Task,
    userMessage: schema.Message,
    history: schema.Message[]
  ): TaskContext {
    return {
      task: { ...task },
      userMessage: userMessage,
      history: [...history],
      isCancelled: () => this.activeCancellations.has(task.id),
    };
  }

  private isValidJsonRpcRequest(body: any): body is schema.JSONRPCRequest {
    return (
      typeof body === "object" &&
      body !== null &&
      body.jsonrpc === "2.0" &&
      typeof body.method === "string" &&
      (body.id === undefined || // Allow undefined for notifications, although A2A methods expect responses
        body.id === null ||
        typeof body.id === "string" ||
        typeof body.id === "number") &&
      (body.params === undefined || typeof body.params === "object") // Allow null, object, array
    );
  }

  // Basic validation helpers (can be expanded)
   private validateTaskIdParams(params: any): asserts params is schema.TaskIdParams {
      if (!params || typeof params !== "object" || typeof params.id !== "string" || params.id === "") {
          throw A2AError.invalidParams("Invalid or missing task ID (params.id).");
      }
  }
  private validateTaskQueryParams(params: any): asserts params is schema.TaskQueryParams {
      this.validateTaskIdParams(params); // Includes ID check
      if (params.historyLength !== undefined && (typeof params.historyLength !== 'number' || params.historyLength < 0)) {
         throw A2AError.invalidParams("Invalid historyLength parameter.");
      }
  }
  private validateTaskSendParams(params: any): asserts params is schema.TaskSendParams {
      this.validateTaskIdParams(params); // Includes ID check
      if (!params.message || typeof params.message !== "object" || !Array.isArray(params.message.parts)) {
          throw A2AError.invalidParams("Invalid or missing message object (params.message).");
      }
      // Add more detailed checks if needed
  }
   private validateTaskPushNotificationConfig(params: any): asserts params is schema.TaskPushNotificationConfig {
       this.validateTaskIdParams(params); // Includes ID check
       if (!params.pushNotificationConfig || typeof params.pushNotificationConfig !== 'object' || typeof params.pushNotificationConfig.url !== 'string') {
            throw A2AError.invalidParams("Invalid pushNotificationConfig object.");
       }
   }

  // --- Response Formatting ---

  private createSuccessResponse<T>(
    id: number | string | null,
    result: T
  ): schema.JSONRPCResponse<T> {
    if (id === null || id === undefined) {
      // ID is required for successful responses in A2A context
      throw A2AError.internalError("Cannot create success response without a valid request ID.");
    }
    return { jsonrpc: "2.0", id: id, result: result };
  }

  private createErrorResponse(
    id: number | string | null,
    error: schema.JSONRPCError<unknown>
  ): schema.JSONRPCResponse<null, unknown> {
    return { jsonrpc: "2.0", id: id ?? null, error: error }; // Use null ID if original was missing/invalid
  }

  private normalizeError(
    error: any,
    reqId: number | string | null,
    taskId?: string
  ): schema.JSONRPCResponse<null, unknown> {
    let a2aError: A2AError;
    if (error instanceof A2AError) {
      a2aError = error;
    } else if (error instanceof Error) {
      a2aError = A2AError.internalError(error.message, { stack: error.stack });
    } else {
      a2aError = A2AError.internalError("An unknown error occurred.", error);
    }
    if (taskId && !a2aError.taskId) a2aError.taskId = taskId;
    console.error(`Error (Task: ${a2aError.taskId ?? "N/A"}, ReqID: ${reqId ?? "N/A"}):`, a2aError);
    return this.createErrorResponse(reqId, a2aError.toJSONRPCError());
  }

  private createTaskStatusEvent(
    taskId: string,
    status: schema.TaskStatus,
    final: boolean
  ): schema.TaskStatusUpdateEvent {
    return { id: taskId, status: status, final: final };
  }

  private createTaskArtifactEvent(
    taskId: string,
    artifact: schema.Artifact
  ): schema.TaskArtifactUpdateEvent {
    // 'final' removed based on schema/previous fix
    return { id: taskId, artifact: artifact };
  }

  private errorHandler = (
    err: any,
    req: Request,
    res: Response,
    next: NextFunction
  ) => {
    if (res.headersSent) {
      console.error(`[ErrorHandler] Error after headers sent (ReqID: ${req.body?.id ?? "N/A"}, TaskID: ${err?.taskId ?? "N/A"}):`, err);
      if (!res.writableEnded) res.end();
      return;
    }

    let responseError: schema.JSONRPCResponse<null, unknown>;
    let reqId: string | number | null = null;
    try { reqId = req.body?.id ?? null; } catch (_) {} // Try to get ID even if body is weird

    if (err instanceof A2AError) {
        responseError = this.normalizeError(err, reqId, err.taskId);
    } else if (err instanceof SyntaxError && "body" in err && "status" in err && err.status === 400) {
        responseError = this.normalizeError(A2AError.parseError(err.message), reqId);
    } else {
        responseError = this.normalizeError(err, reqId);
    }

    // Determine appropriate HTTP status code based on JSON-RPC error code
    let statusCode = 200; // Default for JSON-RPC errors
     if (responseError.error) {
         switch (responseError.error.code) {
             case schema.ErrorCodeParseError:
             case schema.ErrorCodeInvalidRequest:
             case schema.ErrorCodeInvalidParams:
                 statusCode = 400; // Bad Request
                 break;
             case schema.ErrorCodeMethodNotFound:
                 statusCode = 404; // Not Found
                 break;
             case schema.ErrorCodeUnsupportedOperation:
                 statusCode = 501; // Not Implemented
                 break;
             case schema.ErrorCodeTaskNotFound:
                 statusCode = 404; // Not Found (specific A2A)
                 break;
             // Keep others as 500 (Internal Error) or 200 (default)
             case schema.ErrorCodeInternalError:
                  statusCode = 500;
                  break;
         }
     }

    res.status(statusCode);
    res.json(responseError);
  };

  private sendJsonResponse<T>(
    res: Response,
    reqId: number | string | null,
    result: T
  ): void {
    if (reqId === null || reqId === undefined) {
       console.warn("Attempted to send JSON response for a request without a valid ID.");
       // Don't send a response if ID is missing/null for success
       return;
    }
    res.status(200).json(this.createSuccessResponse(reqId, result));
  }
}
