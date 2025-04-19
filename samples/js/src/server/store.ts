import fs from "fs/promises";
import path from "path";
import * as schema from "../schema.js";
import { A2AError } from "./error.js";
import { getCurrentTimestamp } from "./utils.js"; // Assuming utils exists

/** Interface for storing Task and its associated Message history. */
export interface TaskAndHistory {
  task: schema.Task;
  history: schema.Message[];
}

/**
 * Interface for task storage providers.
 * Includes methods for task and history management.
 * Placeholder methods for knowledge graph operations are included.
 */
export interface TaskStore {
  /** Saves task and history. Overwrites if exists. */
  save(data: TaskAndHistory): Promise<void>;

  /** Loads task and history by ID. Returns null if not found. */
  load(taskId: string): Promise<TaskAndHistory | null>;

  // --- Knowledge Graph Methods (Interface) ---
  // These need actual implementations in a KG-enabled store.

  /** Executes a knowledge query (e.g., GraphQL) against the store. */
  knowledgeQuery(
    params: schema.KnowledgeQueryParams
  ): Promise<schema.KnowledgeQueryResponseResult | null>; // Returns result or null

  /** Applies updates (patches) to the knowledge graph. */
  knowledgeUpdate(
    params: schema.KnowledgeUpdateParams
  ): Promise<schema.KnowledgeUpdateResponseResult>; // Returns success/verification

  /**
   * Initiates a subscription to knowledge graph changes.
   * Returns an AsyncIterable yielding change events.
   * The store implementation needs to manage the subscription lifecycle.
   */
  knowledgeSubscribe(
    params: schema.KnowledgeSubscribeParams
  ): AsyncIterable<schema.KnowledgeGraphChangeEvent>;
}

// ========================
// InMemoryTaskStore
// ========================

export class InMemoryTaskStore implements TaskStore {
  private taskStore: Map<string, TaskAndHistory> = new Map();
  // In-memory placeholder for push configs (as used in server.ts fix)
  public _pushConfigs: Record<string, schema.PushNotificationConfig> = {};
  // Placeholder for KG data and subscriptions
  // private knowledgeGraphData: any = {}; // Replace with actual KG structure
  // private knowledgeSubscriptions: Map<string, { params: schema.KnowledgeSubscribeParams, queue: AsyncQueue<schema.KnowledgeGraphChangeEvent> }> = new Map();

  async load(taskId: string): Promise<TaskAndHistory | null> {
    const entry = this.taskStore.get(taskId);
    return entry
      ? { task: { ...entry.task }, history: [...entry.history] }
      : null;
  }

  async save(data: TaskAndHistory): Promise<void> {
    this.taskStore.set(data.task.id, {
      task: { ...data.task },
      history: [...data.history],
    });
    // If save triggers KG changes relevant to subscriptions, push to queues here.
  }

  // --- KG Method Placeholders ---
  async knowledgeQuery(
    params: schema.KnowledgeQueryParams
  ): Promise<schema.KnowledgeQueryResponseResult | null> {
    console.warn(
      `[InMemoryTaskStore] knowledgeQuery called for task ${params.taskId}, but not implemented.`
    );
    throw A2AError.unsupportedOperation(
      "knowledge/query (InMemoryTaskStore)"
    );
    // Example structure if implemented:
    // const results = // ... query internal KG data based on params.query ...
    // return { data: results, queryMetadata: { source: "memory" } };
  }

  async knowledgeUpdate(
    params: schema.KnowledgeUpdateParams
  ): Promise<schema.KnowledgeUpdateResponseResult> {
    console.warn(
      `[InMemoryTaskStore] knowledgeUpdate called for task ${params.taskId}, but not implemented.`
    );
    // Example structure if implemented:
    // Perform verification based on params.metadata, params.justification
    // Apply params.mutations to internal KG data
    // Trigger notifications for relevant subscriptions
    // return { success: true, verificationStatus: "Verified (Placeholder)" };
    throw A2AError.unsupportedOperation(
      "knowledge/update (InMemoryTaskStore)"
    );
  }

  async *knowledgeSubscribe(
    params: schema.KnowledgeSubscribeParams
  ): AsyncIterable<schema.KnowledgeGraphChangeEvent> {
    console.warn(
      `[InMemoryTaskStore] knowledgeSubscribe called for task ${params.taskId}, but not implemented.`
    );
    // This needs a proper pub/sub mechanism tied to knowledgeUpdate.
    // Yielding nothing and throwing immediately.
    if (false) { // Keep yielding type correct for TS
        yield {} as schema.KnowledgeGraphChangeEvent;
    }
    throw A2AError.unsupportedOperation(
      "knowledge/subscribe (InMemoryTaskStore)"
    );
     // Example structure if implemented:
     // const subId = generateSubscriptionId();
     // const queue = new AsyncQueue<schema.KnowledgeGraphChangeEvent>();
     // this.knowledgeSubscriptions.set(subId, { params, queue });
     // try {
     //   for await (const event of queue) {
     //     yield event;
     //   }
     // } finally {
     //   this.knowledgeSubscriptions.delete(subId);
     // }
  }
}

// ========================
// FileStore
// ========================
// FileStore remains largely the same for task/history, KG methods are stubs.

export class FileStore implements TaskStore {
  private baseDir: string;
   // In-memory placeholder for push configs
  public _pushConfigs: Record<string, schema.PushNotificationConfig> = {};

  constructor(options?: { dir?: string }) {
    this.baseDir = options?.dir || ".a2a-tasks";
  }

  private async ensureDirectoryExists(): Promise<void> {
    try {
      await fs.mkdir(this.baseDir, { recursive: true });
    } catch (error: any) {
      throw A2AError.internalError(`Failed to create dir ${this.baseDir}: ${error.message}`, error);
    }
  }

  private getTaskFilePath(taskId: string): string {
    const safeTaskId = path.basename(taskId);
     if (safeTaskId !== taskId || taskId.includes("..")) throw A2AError.invalidParams(`Invalid Task ID: ${taskId}`);
    return path.join(this.baseDir, `${safeTaskId}.json`);
  }

  private getHistoryFilePath(taskId: string): string {
    const safeTaskId = path.basename(taskId);
     if (safeTaskId !== taskId || taskId.includes("..")) throw A2AError.invalidParams(`Invalid Task ID: ${taskId}`);
    return path.join(this.baseDir, `${safeTaskId}.history.json`);
  }

  private isHistoryFileContent(content: any): content is { messageHistory: schema.Message[] } {
    return typeof content === "object" && content !== null && Array.isArray(content.messageHistory);
  }

   private async readJsonFile<T>(filePath: string): Promise<T | null> {
    try {
      const data = await fs.readFile(filePath, "utf8");
      return JSON.parse(data) as T;
    } catch (error: any) {
      if (error.code === "ENOENT") return null;
      throw A2AError.internalError(`Failed to read ${filePath}: ${error.message}`, error);
    }
  }

  private async writeJsonFile(filePath: string, data: any): Promise<void> {
    try {
      await this.ensureDirectoryExists();
      await fs.writeFile(filePath, JSON.stringify(data, null, 2), "utf8");
    } catch (error: any) {
      throw A2AError.internalError(`Failed to write ${filePath}: ${error.message}`, error);
    }
  }

  async load(taskId: string): Promise<TaskAndHistory | null> {
    const taskFilePath = this.getTaskFilePath(taskId);
    const historyFilePath = this.getHistoryFilePath(taskId);

    const task = await this.readJsonFile<schema.Task>(taskFilePath);
    if (!task) return null;

    let history: schema.Message[] = [];
    try {
      const historyContent = await this.readJsonFile<unknown>(historyFilePath);
      if (this.isHistoryFileContent(historyContent)) {
        history = historyContent.messageHistory;
      } else if (historyContent !== null) {
        console.warn(`[FileStore] Malformed history file ${historyFilePath}.`);
      }
    } catch (error) {
      console.error(`[FileStore] Error reading history ${historyFilePath}:`, error);
    }

    return { task, history };
  }

  async save(data: TaskAndHistory): Promise<void> {
    const { task, history } = data;
    const taskFilePath = this.getTaskFilePath(task.id);
    const historyFilePath = this.getHistoryFilePath(task.id);
    await this.ensureDirectoryExists();
    await Promise.all([
      this.writeJsonFile(taskFilePath, task),
      this.writeJsonFile(historyFilePath, { messageHistory: history }),
    ]);
     // If save triggers KG changes relevant to subscriptions, push to queues here.
  }

   // --- KG Method Placeholders ---
  async knowledgeQuery(params: schema.KnowledgeQueryParams): Promise<schema.KnowledgeQueryResponseResult | null> {
      console.warn(`[FileStore] knowledgeQuery called for task ${params.taskId}, but not implemented.`);
      throw A2AError.unsupportedOperation("knowledge/query (FileStore)");
  }

  async knowledgeUpdate(params: schema.KnowledgeUpdateParams): Promise<schema.KnowledgeUpdateResponseResult> {
      console.warn(`[FileStore] knowledgeUpdate called for task ${params.taskId}, but not implemented.`);
      throw A2AError.unsupportedOperation("knowledge/update (FileStore)");
  }

  async *knowledgeSubscribe(params: schema.KnowledgeSubscribeParams): AsyncIterable<schema.KnowledgeGraphChangeEvent> {
      console.warn(`[FileStore] knowledgeSubscribe called for task ${params.taskId}, but not implemented.`);
      if (false) yield {} as schema.KnowledgeGraphChangeEvent; // Keep yield type correct
      throw A2AError.unsupportedOperation("knowledge/subscribe (FileStore)");
  }
}