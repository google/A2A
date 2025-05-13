import express, {
  Request,
  Response,
  NextFunction,
  RequestHandler,
} from "express";
import cors, { CorsOptions } from "cors";
import * as schema from "../schema.js";
// Import TaskAndHistory along with TaskStore implementations
import { TaskStore, InMemoryTaskStore, TaskAndHistory } from "./store.js";
// Import TaskHandler and the original TaskContext to derive the new one
import { TaskHandler, TaskContext as OldTaskContext } from "./handler.js";
import { A2AError, errorHandler, normalizeError } from "./error.js";
import {
  getCurrentTimestamp,
  isTaskStatusUpdate,
  isArtifactUpdate,
} from "./utils.js";

/**
 * Options for configuring the A2AServer.
 */
export interface A2AServerOptions {
  /** Task storage implementation. Defaults to InMemoryTaskStore. */
  taskStore?: TaskStore;
  /** CORS configuration options or boolean/string. Defaults to allowing all origins. */
  cors?: CorsOptions | boolean | string;
  /** Base path for the A2A endpoint. Defaults to '/'. */
  basePath?: string;
  /** Agent Card for the agent being served. */
  card?: schema.AgentCard;
}

// Define new TaskContext without the store, based on the original from handler.ts
export interface TaskContext extends Omit<OldTaskContext, "taskStore"> {}

/**
 * Implements an A2A specification compliant server using Express.
 */
export class A2AServer {
  private taskHandler: TaskHandler;
  private taskStore: TaskStore;
  private corsOptions: CorsOptions | boolean | string;
  private basePath: string;
  // Track active cancellations
  private activeCancellations: Set<string> = new Set();
  card: schema.AgentCard;

  // Helper to apply updates (status or artifact) immutably
  private applyUpdateToTaskAndHistory(
    current: TaskAndHistory,
    update: Omit<schema.TaskStatus, "timestamp"> | schema.Artifact
  ): TaskAndHistory {
    let newTask = { ...current.task }; // Shallow copy task
    let newHistory = [...current.history]; // Shallow copy history

    if (isTaskStatusUpdate(update)) {
      // Merge status update
      newTask.status = {
        ...newTask.status, // Keep existing properties if not overwritten
        ...update, // Apply updates
        timestamp: getCurrentTimestamp(), // Always update timestamp
      };
      // If the update includes an agent message, add it to history
      if (update.message?.role === "agent") {
        newHistory.push(update.message);
      }
    } else if (isArtifactUpdate(update)) {
      // Handle artifact update
      if (!newTask.artifacts) {
        newTask.artifacts = [];
      } else {
        // Ensure we're working with a copy of the artifacts array
        newTask.artifacts = [...newTask.artifacts];
      }

      const existingIndex = update.index ?? -1; // Use index if provided
      let replaced = false;

      if (existingIndex >= 0 && existingIndex < newTask.artifacts.length) {
        const existingArtifact = newTask.artifacts[existingIndex];
        if (update.append) {
          // Create a deep copy for modification to avoid mutating original
          const appendedArtifact = JSON.parse(JSON.stringify(existingArtifact));
          appendedArtifact.parts.push(...update.parts);
          if (update.metadata) {
            appendedArtifact.metadata = {
              ...(appendedArtifact.metadata || {}),
              ...update.metadata,
            };
          }
          if (update.lastChunk !== undefined)
            appendedArtifact.lastChunk = update.lastChunk;
          if (update.description)
            appendedArtifact.description = update.description;
          newTask.artifacts[existingIndex] = appendedArtifact; // Replace with appended version
          replaced = true;
        } else {
          // Overwrite artifact at index (with a copy of the update)
          newTask.artifacts[existingIndex] = { ...update };
          replaced = true;
        }
      } else if (update.name) {
        const namedIndex = newTask.artifacts.findIndex(
          (a) => a.name === update.name
        );
        if (namedIndex >= 0) {
          newTask.artifacts[namedIndex] = { ...update }; // Replace by name (with copy)
          replaced = true;
        }
      }

      if (!replaced) {
        newTask.artifacts.push({ ...update }); // Add as a new artifact (copy)
        // Sort if indices are present
        if (newTask.artifacts.some((a) => a.index !== undefined)) {
          newTask.artifacts.sort((a, b) => (a.index ?? 0) - (b.index ?? 0));
        }
      }
    }

    return { task: newTask, history: newHistory };
  }

  constructor(handler: TaskHandler, options: A2AServerOptions = {}) {
    this.taskHandler = handler;
    this.taskStore = options.taskStore ?? new InMemoryTaskStore();
    this.corsOptions = options.cors ?? true; // Default to allow all
    this.basePath = options.basePath ?? "/";
    if (options.card) this.card = options.card;
    // Ensure base path starts and ends with a slash if it's not just "/"
    if (this.basePath !== "/") {
      this.basePath = `/${this.basePath.replace(/^\/|\/$/g, "")}/`;
    }
  }

  /**
   * Starts the Express server listening on the specified port.
   * @param port Port number to listen on. Defaults to 41241.
   * @returns The running Express application instance.
   */
  start(port = 41241): express.Express {
    const app = express();

    // Configure CORS
    if (this.corsOptions !== false) {
      const options =
        typeof this.corsOptions === "string"
          ? { origin: this.corsOptions }
          : this.corsOptions === true
          ? undefined // Use default cors options if true
          : this.corsOptions;
      app.use(cors(options));
    }

    // Middleware
    app.use(express.json()); // Parse JSON bodies

    app.get("/.well-known/agent.json", (req, res) => {
      res.json(this.card);
    });

    // Mount the endpoint handler
    app.post(this.basePath, this.endpoint());

    // Basic error handler
    app.use(errorHandler);

    // Start listening
    app.listen(port, () => {
      console.log(
        `A2A Server listening on port ${port} at path ${this.basePath}`
      );
    });

    return app;
  }

  /**
   * Returns an Express RequestHandler function to handle A2A requests.
   */
  endpoint(): RequestHandler {
    return async (req: Request, res: Response, next: NextFunction) => {
      const requestBody = req.body;
      let taskId: string | undefined; // For error context

      try {
        // 1. Validate basic JSON-RPC structure
        if (!this.isValidJsonRpcRequest(requestBody)) {
          throw A2AError.invalidRequest("Invalid JSON-RPC request structure.");
        }
        // Attempt to get task ID early for error context. Cast params to any to access id.
        // Proper validation happens within specific handlers.
        taskId = (requestBody.params as any)?.id;

        // 2. Route based on method
        switch (requestBody.method) {
          case "tasks/send":
            await this.handleTaskSend(
              requestBody as schema.SendTaskRequest,
              res
            );
            break;
          case "tasks/sendSubscribe":
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
          // Add other methods like tasks/pushNotification/*, tasks/resubscribe later if needed
          default:
            throw A2AError.methodNotFound(requestBody.method);
        }
      } catch (error) {
        // Forward errors to the Express error handler
        if (error instanceof A2AError && taskId && !error.taskId) {
          error.taskId = taskId; // Add task ID context if missing
        }
        next(normalizeError(error, requestBody?.id ?? null));
      }
    };
  }

  // --- Request Handlers ---

  private async handleTaskSend(
    req: schema.SendTaskRequest,
    res: Response
  ): Promise<void> {
    this.validateTaskSendParams(req.params);
    const { id: taskId, message, sessionId, metadata } = req.params;

    // Load or create task AND history
    let currentData = await this.loadOrCreateTaskAndHistory(
      taskId,
      message,
      sessionId,
      metadata
    );
    // Use the new TaskContext definition, passing history
    const context = this.createTaskContext(
      currentData.task,
      message,
      currentData.history
    );
    const generator = this.taskHandler(context);

    // Process generator yields
    try {
      for await (const yieldValue of generator) {
        // Apply update immutably
        currentData = this.applyUpdateToTaskAndHistory(currentData, yieldValue);
        // Save the updated state
        await this.taskStore.save(currentData);
        // Update context snapshot for next iteration
        context.task = currentData.task;
      }
    } catch (handlerError) {
      // If handler throws, apply 'failed' status, save, and rethrow
      const failureStatusUpdate: Omit<schema.TaskStatus, "timestamp"> = {
        state: "failed",
        message: {
          role: "agent",
          parts: [
            {
              text: `Handler failed: ${
                handlerError instanceof Error
                  ? handlerError.message
                  : String(handlerError)
              }`,
            },
          ],
        },
      };
      currentData = this.applyUpdateToTaskAndHistory(
        currentData,
        failureStatusUpdate
      );
      try {
        await this.taskStore.save(currentData);
      } catch (saveError) {
        console.error(
          `Failed to save task ${taskId} after handler error:`,
          saveError
        );
        // Still throw the original handler error
      }
      throw normalizeError(handlerError, req.id, taskId); // Rethrow original error
    }

    // The loop finished, send the final task state
    this.sendJsonResponse(res, req.id, currentData.task);
  }

  private async handleTaskSendSubscribe(
    req: schema.SendTaskStreamingRequest,
    res: Response
  ): Promise<void> {
    this.validateTaskSendParams(req.params);
    const { id: taskId, message, sessionId, metadata } = req.params;

    // Load or create task AND history
    let currentData = await this.loadOrCreateTaskAndHistory(
      taskId,
      message,
      sessionId,
      metadata
    );
    // Use the new TaskContext definition, passing history
    const context = this.createTaskContext(
      currentData.task,
      message,
      currentData.history
    );
    const generator = this.taskHandler(context);

    // --- Setup SSE ---
    res.writeHead(200, {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
      // Optional: "Access-Control-Allow-Origin": "*" // Handled by cors middleware usually
    });
    // Function to send SSE data
    const sendEvent = (eventData: schema.JSONRPCResponse) => {
      res.write(`data: ${JSON.stringify(eventData)}\n\n`);
    };

    let lastEventWasFinal = false; // Track if the last sent event was marked final

    try {
      // Optionally send initial state?
      // sendEvent(this.createSuccessResponse(req.id, this.createTaskStatusEvent(taskId, currentData.task.status, false)));

      // Process generator yields
      for await (const yieldValue of generator) {
        // Apply update immutably
        currentData = this.applyUpdateToTaskAndHistory(currentData, yieldValue);
        // Save the updated state
        await this.taskStore.save(currentData);
        // Update context snapshot
        context.task = currentData.task;

        let event:
          | schema.TaskStatusUpdateEvent
          | schema.TaskArtifactUpdateEvent;
        let isFinal = false;

        // Determine event type and check for final state based on the *updated* task
        if (isTaskStatusUpdate(yieldValue)) {
          const terminalStates: schema.TaskState[] = [
            "completed",
            "failed",
            "canceled",
            "input-required", // Treat input-required as potentially final for streaming?
          ];
          isFinal = terminalStates.includes(currentData.task.status.state);
          event = this.createTaskStatusEvent(
            taskId,
            currentData.task.status,
            isFinal
          );
          if (isFinal) {
            console.log(
              `[SSE ${taskId}] Yielded terminal state ${currentData.task.status.state}, marking event as final.`
            );
          }
        } else if (isArtifactUpdate(yieldValue)) {
          // Find the updated artifact in the new task object
          const updatedArtifact =
            currentData.task.artifacts?.find(
              (a) =>
                (a.index !== undefined && a.index === yieldValue.index) ||
                (a.name && a.name === yieldValue.name)
            ) ?? yieldValue; // Fallback
          event = this.createTaskArtifactEvent(taskId, updatedArtifact, false);
          // Note: Artifact updates themselves don't usually mark the task as final.
        } else {
          console.warn("[SSE] Handler yielded unknown value:", yieldValue);
          continue; // Skip sending an event for unknown yields
        }

        sendEvent(this.createSuccessResponse(req.id, event));
        lastEventWasFinal = isFinal;

        // If the status update resulted in a final state, stop processing
        if (isFinal) break;
      }

      // Loop finished. Check if a final event was already sent.
      if (!lastEventWasFinal) {
        console.log(
          `[SSE ${taskId}] Handler finished without yielding terminal state. Sending final state: ${currentData.task.status.state}`
        );
        // Ensure the task is actually in a recognized final state before sending.
        const finalStates: schema.TaskState[] = [
          "completed",
          "failed",
          "canceled",
          "input-required", // Consider input-required final for SSE end?
        ];
        if (!finalStates.includes(currentData.task.status.state)) {
          console.warn(
            `[SSE ${taskId}] Task ended non-terminally (${currentData.task.status.state}). Forcing 'completed'.`
          );
          // Apply 'completed' state update
          currentData = this.applyUpdateToTaskAndHistory(currentData, {
            state: "completed",
          });
          // Save the forced final state
          await this.taskStore.save(currentData);
        }
        // Send the final status event
        const finalEvent = this.createTaskStatusEvent(
          taskId,
          currentData.task.status,
          true // Mark as final
        );
        sendEvent(this.createSuccessResponse(req.id, finalEvent));
      }
    } catch (handlerError) {
      // Handler threw an error
      console.error(
        `[SSE ${taskId}] Handler error during streaming:`,
        handlerError
      );
      // Apply 'failed' status update
      const failureUpdate: Omit<schema.TaskStatus, "timestamp"> = {
        state: "failed",
        message: {
          role: "agent",
          parts: [
            {
              text: `Handler failed: ${
                handlerError instanceof Error
                  ? handlerError.message
                  : String(handlerError)
              }`,
            },
          ],
        },
      };
      currentData = this.applyUpdateToTaskAndHistory(
        currentData,
        failureUpdate
      );

      try {
        // Save the failed state
        await this.taskStore.save(currentData);
      } catch (saveError) {
        console.error(
          `[SSE ${taskId}] Failed to save task after handler error:`,
          saveError
        );
      }

      // Send final error status event via SSE
      const errorEvent = this.createTaskStatusEvent(
        taskId,
        currentData.task.status, // Use the updated status
        true // Mark as final
      );
      sendEvent(this.createSuccessResponse(req.id, errorEvent));

      // Note: We don't send a JSON-RPC error response here, the error is signaled via the event stream.
    } finally {
      // End the SSE stream if it hasn't already been closed by sending a final event
      if (!res.writableEnded) {
        res.end();
      }
    }
  }

  private async handleTaskGet(
    req: schema.GetTaskRequest,
    res: Response
  ): Promise<void> {
    const { id: taskId } = req.params;
    if (!taskId) throw A2AError.invalidParams("Missing task ID.");

    // Load both task and history
    const data = await this.taskStore.load(taskId);
    if (!data) {
      throw A2AError.taskNotFound(taskId);
    }
    // Return only the task object as per spec
    this.sendJsonResponse(res, req.id, data.task);
  }

  private async handleTaskCancel(
    req: schema.CancelTaskRequest,
    res: Response
  ): Promise<void> {
    const { id: taskId } = req.params;
    if (!taskId) throw A2AError.invalidParams("Missing task ID.");

    // Load task and history
    let data = await this.taskStore.load(taskId);
    if (!data) {
      throw A2AError.taskNotFound(taskId);
    }

    // Check if cancelable (not already in a final state)
    const finalStates: schema.TaskState[] = ["completed", "failed", "canceled"];
    if (finalStates.includes(data.task.status.state)) {
      console.log(
        `Task ${taskId} already in final state ${data.task.status.state}, cannot cancel.`
      );
      this.sendJsonResponse(res, req.id, data.task); // Return current state
      return;
    }

    // Signal cancellation
    this.activeCancellations.add(taskId);

    // Apply 'canceled' state update
    const cancelUpdate: Omit<schema.TaskStatus, "timestamp"> = {
      state: "canceled",
      message: {
        role: "agent",
        parts: [{ text: "Task cancelled by request." }],
      },
    };
    data = this.applyUpdateToTaskAndHistory(data, cancelUpdate);

    // Save the updated state
    await this.taskStore.save(data);

    // Remove from active cancellations *after* saving
    this.activeCancellations.delete(taskId);

    // Return the updated task object
    this.sendJsonResponse(res, req.id, data.task);
  }

  // --- Helper Methods ---

  // Renamed and updated to handle both task and history
  private async loadOrCreateTaskAndHistory(
    taskId: string,
    initialMessage: schema.Message,
    sessionId?: string | null, // Allow null
    metadata?: Record<string, unknown> | null // Allow null
  ): Promise<TaskAndHistory> {
    let data = await this.taskStore.load(taskId);
    let needsSave = false;

    if (!data) {
      // Create new task and history
      const initialTask: schema.Task = {
        id: taskId,
        sessionId: sessionId ?? undefined, // Store undefined if null
        status: {
          state: "submitted", // Start as submitted
          timestamp: getCurrentTimestamp(),
          message: null, // Initial user message goes only to history for now
        },
        artifacts: [],
        metadata: metadata ?? undefined, // Store undefined if null
      };
      const initialHistory: schema.Message[] = [initialMessage]; // History starts with user message
      data = { task: initialTask, history: initialHistory };
      needsSave = true; // Mark for saving
      console.log(`[Task ${taskId}] Created new task and history.`);
    } else {
      console.log(`[Task ${taskId}] Loaded existing task and history.`);
      // Add current user message to history
      // Make a copy before potentially modifying
      data = { task: data.task, history: [...data.history, initialMessage] };
      needsSave = true; // History updated, mark for saving

      // Handle state transitions for existing tasks
      const finalStates: schema.TaskState[] = [
        "completed",
        "failed",
        "canceled",
      ];
      if (finalStates.includes(data.task.status.state)) {
        console.warn(
          `[Task ${taskId}] Received message for task already in final state ${data.task.status.state}. Handling as new submission (keeping history).`
        );
        // Option 1: Reset state to 'submitted' (keeps history, effectively restarts)
        const resetUpdate: Omit<schema.TaskStatus, "timestamp"> = {
          state: "submitted",
          message: null, // Clear old agent message
        };
        data = this.applyUpdateToTaskAndHistory(data, resetUpdate);
        // needsSave is already true

        // Option 2: Throw error (stricter)
        // throw A2AError.invalidRequest(`Task ${taskId} is already in a final state.`);
      } else if (data.task.status.state === "input-required") {
        console.log(
          `[Task ${taskId}] Received message while 'input-required', changing state to 'working'.`
        );
        // If it was waiting for input, update state to 'working'
        const workingUpdate: Omit<schema.TaskStatus, "timestamp"> = {
          state: "working",
        };
        data = this.applyUpdateToTaskAndHistory(data, workingUpdate);
        // needsSave is already true
      } else if (data.task.status.state === "working") {
        // If already working, maybe warn but allow? Or force back to submitted?
        console.warn(
          `[Task ${taskId}] Received message while already 'working'. Proceeding.`
        );
        // No state change needed, but history was updated, so needsSave is true.
      }
      // If 'submitted', receiving another message might be odd, but proceed.
    }

    // Save if created or modified before returning
    if (needsSave) {
      await this.taskStore.save(data);
    }

    // Return copies to prevent mutation by caller before handler runs
    return { task: { ...data.task }, history: [...data.history] };
  }

  // Update context creator to accept and include history
  private createTaskContext(
    task: schema.Task,
    userMessage: schema.Message,
    history: schema.Message[] // Add history parameter
  ): TaskContext {
    return {
      task: { ...task }, // Pass a copy
      userMessage: userMessage,
      history: [...history], // Pass a copy of the history
      isCancelled: () => this.activeCancellations.has(task.id),
      // taskStore is removed
    };
  }

  private isValidJsonRpcRequest(body: any): body is schema.JSONRPCRequest {
    return (
      typeof body === "object" &&
      body !== null &&
      body.jsonrpc === "2.0" &&
      typeof body.method === "string" &&
      (body.id === null ||
        typeof body.id === "string" ||
        typeof body.id === "number") && // ID is required for requests needing response
      (body.params === undefined ||
        typeof body.params === "object" || // Allows null, array, or object
        Array.isArray(body.params))
    );
  }

  private validateTaskSendParams(
    params: any
  ): asserts params is schema.TaskSendParams {
    if (!params || typeof params !== "object") {
      throw A2AError.invalidParams("Missing or invalid params object.");
    }
    if (typeof params.id !== "string" || params.id === "") {
      throw A2AError.invalidParams("Invalid or missing task ID (params.id).");
    }
    if (
      !params.message ||
      typeof params.message !== "object" ||
      !Array.isArray(params.message.parts)
    ) {
      throw A2AError.invalidParams(
        "Invalid or missing message object (params.message)."
      );
    }
    // Add more checks for message structure, sessionID, metadata, etc. if needed
  }

  // --- Response Formatting ---

  private createSuccessResponse<T>(
    id: number | string | null,
    result: T
  ): schema.JSONRPCResponse<T> {
    if (id === null) {
      // This shouldn't happen for methods that expect a response, but safeguard
      throw A2AError.internalError(
        "Cannot create success response for null ID."
      );
    }
    return {
      jsonrpc: "2.0",
      id: id,
      result: result,
    };
  }

  /** Creates a TaskStatusUpdateEvent object */
  private createTaskStatusEvent(
    taskId: string,
    status: schema.TaskStatus,
    final: boolean
  ): schema.TaskStatusUpdateEvent {
    return {
      id: taskId,
      status: status, // Assumes status already has timestamp from applyUpdate
      final: final,
    };
  }

  /** Creates a TaskArtifactUpdateEvent object */
  private createTaskArtifactEvent(
    taskId: string,
    artifact: schema.Artifact,
    final: boolean
  ): schema.TaskArtifactUpdateEvent {
    return {
      id: taskId,
      artifact: artifact,
      final: final, // Usually false unless it's the very last thing
    };
  }

  /** Sends a standard JSON success response */
  private sendJsonResponse<T>(
    res: Response,
    reqId: number | string | null,
    result: T
  ): void {
    if (reqId === null) {
      console.warn(
        "Attempted to send JSON response for a request with null ID."
      );
      // Should this be an error? Or just log and ignore?
      // For 'tasks/send' etc., ID should always be present.
      return;
    }
    res.json(this.createSuccessResponse(reqId, result));
  }
}
