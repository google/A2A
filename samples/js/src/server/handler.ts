import * as schema from "../schema.js";

/**
 * Context object provided to the TaskHandler.
 */
export interface TaskContext {
  /**
   * The current state of the task when the handler is invoked or resumed.
   * Note: This is a snapshot. For the absolute latest state during async operations,
   * the handler might need to reload the task via the store.
   */
  task: schema.Task;

  /**
   * The specific user message that triggered this handler invocation or resumption.
   */
  userMessage: schema.Message;

  /**
   * Function to check if cancellation has been requested for this task.
   * Handlers should ideally check this periodically during long-running operations.
   * @returns {boolean} True if cancellation has been requested, false otherwise.
   */
  isCancelled(): boolean;

  /**
   * The message history associated with the task up to the point the handler is invoked.
   * Optional, as history might not always be available or relevant.
   */
  history?: schema.Message[];

  // taskStore is removed as the server now handles loading/saving directly.
  // If a handler specifically needs history, it would need to be passed differently
  // or the handler pattern might need adjustment based on use case.

  // Potential future additions:
  // - logger instance
  // - AbortSignal linked to cancellation
}

/**
 * Represents the possible types of updates a TaskHandler can yield.
 * It's either a partial TaskStatus (without the server-managed timestamp)
 * or a complete Artifact object.
 */
export type TaskYieldUpdate =
  | Omit<schema.TaskStatus, "timestamp">
  | schema.Artifact;

/**
 * Defines the signature for a task handler function.
 *
 * Handlers are implemented as async generators. They receive context about the
 * task and the triggering message. They can perform work and `yield` status
 * or artifact updates (`TaskYieldUpdate`). The server consumes these yields,
 * updates the task state in the store, and streams events if applicable.
 *
 * @param context - The TaskContext object containing task details, cancellation status, and store access.
 * @yields {TaskYieldUpdate} - Updates to the task's status or artifacts.
 * @returns {Promise<schema.Task | void>} - Optionally returns the final complete Task object
 *   (needed for non-streaming 'tasks/send'). If void is returned, the server uses the
 *   last known state from the store after processing all yields.
 */
export type TaskHandler = (
  context: TaskContext
) => AsyncGenerator<TaskYieldUpdate, schema.Task | void, unknown>;
