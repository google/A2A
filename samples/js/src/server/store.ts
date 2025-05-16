import fs from "fs/promises";
import path from "path";
import * as schema from "../schema.js";
import { A2AError } from "./error.js";
import {
  getCurrentTimestamp,
  isArtifactUpdate,
  isTaskStatusUpdate,
} from "./utils.js";

// Helper type for the simplified store
export interface TaskAndHistory {
  task: schema.Task;
  history: schema.Message[];
}

/**
 * Simplified interface for task storage providers.
 * Stores and retrieves both the task and its full message history together.
 */
export interface TaskStore {
  /**
   * Saves a task and its associated message history.
   * Overwrites existing data if the task ID exists.
   * @param data An object containing the task and its history.
   * @returns A promise resolving when the save operation is complete.
   */
  save(data: TaskAndHistory): Promise<void>;

  /**
   * Loads a task and its history by task ID.
   * @param taskId The ID of the task to load.
   * @returns A promise resolving to an object containing the Task and its history, or undefined if not found.
   */
  load(taskId: string): Promise<TaskAndHistory | undefined>;
}

// ========================
// InMemoryTaskStore
// ========================

// Use TaskAndHistory directly for storage
export class InMemoryTaskStore implements TaskStore {
  private store: Map<string, TaskAndHistory> = new Map();

  async load(taskId: string): Promise<TaskAndHistory | undefined> {
    const entry = this.store.get(taskId);
    // Return copies to prevent external mutation
    return entry
      ? { task: { ...entry.task }, history: [...entry.history] }
      : undefined;
  }

  async save(data: TaskAndHistory): Promise<void> {
    // Store copies to prevent internal mutation if caller reuses objects
    this.store.set(data.task.id, {
      task: { ...data.task },
      history: [...data.history],
    });
  }
}

// ========================
// FileStore
// ========================

export class FileStore implements TaskStore {
  private baseDir: string;

  constructor(options?: { dir?: string }) {
    // Default directory relative to the current working directory
    this.baseDir = options?.dir || ".a2a-tasks";
  }

  private async ensureDirectoryExists(): Promise<void> {
    try {
      await fs.mkdir(this.baseDir, { recursive: true });
    } catch (error: any) {
      throw A2AError.internalError(
        `Failed to create directory ${this.baseDir}: ${error.message}`,
        error,
      );
    }
  }

  private getTaskFilePath(taskId: string): string {
    // Sanitize taskId to prevent directory traversal
    const safeTaskId = path.basename(taskId);
    return path.join(this.baseDir, `${safeTaskId}.json`);
  }

  private getHistoryFilePath(taskId: string): string {
    // Sanitize taskId
    const safeTaskId = path.basename(taskId);
    if (safeTaskId !== taskId || taskId.includes("..")) {
      throw A2AError.invalidParams(`Invalid Task ID format: ${taskId}`);
    }
    return path.join(this.baseDir, `${safeTaskId}.history.json`);
  }

  // Type guard for history file content
  private isHistoryFileContent(
    content: any,
  ): content is { messageHistory: schema.Message[] } {
    return (
      !!content &&
      typeof content === "object" &&
      Array.isArray(content.messageHistory) &&
      // Optional: Add deeper validation of message structure if needed
      content.messageHistory.every(
        (msg: any) => typeof msg === "object" && msg.role && msg.parts,
      )
    );
  }

  private async readJsonFile<T>(filePath: string): Promise<T | undefined> {
    try {
      const data = await fs.readFile(filePath, "utf8");
      return JSON.parse(data) as T;
    } catch (error: any) {
      if (error.code === "ENOENT") {
        return undefined; // File not found is not an error for loading
      }
      throw A2AError.internalError(
        `Failed to read file ${filePath}: ${error.message}`,
        error,
      );
    }
  }

  private async writeJsonFile(filePath: string, data: any): Promise<void> {
    try {
      await this.ensureDirectoryExists();
      await fs.writeFile(filePath, JSON.stringify(data, null, 2), "utf8");
    } catch (error: any) {
      throw A2AError.internalError(
        `Failed to write file ${filePath}: ${error.message}`,
        error,
      );
    }
  }

  async load(taskId: string): Promise<TaskAndHistory | undefined> {
    const taskFilePath = this.getTaskFilePath(taskId);
    const historyFilePath = this.getHistoryFilePath(taskId);

    // Read task file first - if it doesn't exist, the task doesn't exist.
    const task = await this.readJsonFile<schema.Task>(taskFilePath);
    if (!task) {
      return undefined; // Task not found
    }

    // Task exists, now try to read history. It might not exist yet.
    let history: schema.Message[] = [];
    try {
      const historyContent = await this.readJsonFile<unknown>(historyFilePath);
      // Validate the structure slightly
      if (this.isHistoryFileContent(historyContent)) {
        history = historyContent.messageHistory;
      } else if (historyContent !== undefined) {
        // Log a warning if the history file exists but is malformed
        console.warn(
          `[FileStore] Malformed history file found for task ${taskId} at ${historyFilePath}. Ignoring content.`,
        );
        // Attempt to delete or rename the malformed file? Or just proceed with empty history.
        // For now, proceed with empty. A 'save' will overwrite it correctly later.
      }
      // If historyContent is undefined (file not found), history remains []
    } catch (error) {
      // Log error reading history but proceed with empty history
      console.error(
        `[FileStore] Error reading history file for task ${taskId}:`,
        error,
      );
      // Proceed with empty history
    }

    return { task, history };
  }

  async save(data: TaskAndHistory): Promise<void> {
    const { task, history } = data;
    const taskFilePath = this.getTaskFilePath(task.id);
    const historyFilePath = this.getHistoryFilePath(task.id);

    // Ensure directory exists (writeJsonFile does this, but good practice)
    await this.ensureDirectoryExists();

    // Write both files - potentially in parallel
    await Promise.all([
      this.writeJsonFile(taskFilePath, task),
      this.writeJsonFile(historyFilePath, { messageHistory: history }),
    ]);
  }
}
