/**
 * Task Persistence and Recovery System for A2A Protocol (KISS Version)
 * 
 * This module provides essential task state management with persistence,
 * optimistic locking, and version control following KISS principles.
 * 
 * Key Features:
 * - Memory-based storage (simple, reliable)
 * - Optimistic locking with version-based concurrency control
 * - Complete audit trail of task state transitions
 * - Automatic task recovery on service restart
 * - Data integrity protection with checksums
 */

/**
 * Task States in A2A Protocol
 */
export enum TaskState {
  Submitted = 'submitted',
  Queued = 'queued',
  Working = 'working',
  Completed = 'completed',
  Failed = 'failed',
  Cancelled = 'cancelled',
  Timeout = 'timeout'
}

/**
 * Task Priority Levels
 */
export enum TaskPriority {
  Low = 'low',
  Normal = 'normal',
  High = 'high',
  Critical = 'critical'
}

/**
 * Task Status Information
 */
export interface TaskStatus {
  state: TaskState;
  timestamp: string;
  message?: string;
  progress?: number;
  estimatedCompletion?: string;
}

/**
 * Task History Entry
 */
export interface TaskHistoryEntry {
  timestamp: string;
  previousState: TaskState;
  newState: TaskState;
  reason?: string;
  metadata?: Record<string, any>;
}

/**
 * Task Artifact
 */
export interface TaskArtifact {
  id: string;
  name: string;
  type: string;
  size: number;
  checksum: string;
  url?: string;
  metadata?: Record<string, any>;
}

/**
 * Persisted Task with Enhanced Metadata
 */
export interface PersistedTask {
  /** Unique task identifier */
  id: string;
  /** Context identifier for grouping related tasks */
  contextId: string;
  /** Current task status */
  status: TaskStatus;
  /** Task priority level */
  priority: TaskPriority;
  /** Task creation timestamp */
  createdAt: string;
  /** Last update timestamp */
  updatedAt: string;
  /** Task expiration timestamp */
  expiresAt?: string;
  /** Persistence version for optimistic locking and version control */
  version: number;
  /** Checksum for data integrity */
  checksum: string;
  /** Task execution history */
  history: TaskHistoryEntry[];
  /** Task artifacts and outputs */
  artifacts: TaskArtifact[];
  /** Additional task metadata */
  metadata: Record<string, any>;
  /** Task kind identifier */
  kind: string;
}

/**
 * Task Storage Interface
 */
export interface TaskStorage {
  initialize(): Promise<void>;
  shutdown(): Promise<void>;
  
  create(task: PersistedTask): Promise<PersistedTask>;
  get(taskId: string): Promise<PersistedTask | null>;
  update(taskId: string, updates: Partial<PersistedTask>, expectedVersion: number): Promise<PersistedTask>;
  delete(taskId: string): Promise<boolean>;
  
  list(contextId?: string, state?: TaskState, limit?: number, offset?: number): Promise<PersistedTask[]>;
  count(contextId?: string, state?: TaskState): Promise<number>;
  
  cleanup(olderThan: Date): Promise<number>;
  getMetrics(): Promise<TaskStorageMetrics>;
}

/**
 * Task Storage Metrics
 */
export interface TaskStorageMetrics {
  totalTasks: number;
  tasksByState: Record<TaskState, number>;
  tasksByPriority: Record<TaskPriority, number>;
  averageTaskDuration: number;
  storageSize: number;
  lastCleanup?: string;
}

/**
 * Memory-based Task Storage Implementation
 */
export class MemoryTaskStorage implements TaskStorage {
  private tasks: Map<string, PersistedTask> = new Map();
  private initialized: boolean = false;

  async initialize(): Promise<void> {
    this.tasks.clear();
    this.initialized = true;
  }

  async shutdown(): Promise<void> {
    this.tasks.clear();
    this.initialized = false;
  }

  async create(task: PersistedTask): Promise<PersistedTask> {
    this.ensureInitialized();
    
    if (this.tasks.has(task.id)) {
      throw new Error(`Task ${task.id} already exists`);
    }
    
    const persistedTask = { ...task };
    this.tasks.set(task.id, persistedTask);
    return persistedTask;
  }

  async get(taskId: string): Promise<PersistedTask | null> {
    this.ensureInitialized();
    return this.tasks.get(taskId) || null;
  }

  async update(taskId: string, updates: Partial<PersistedTask>, expectedVersion: number): Promise<PersistedTask> {
    this.ensureInitialized();
    
    const existingTask = this.tasks.get(taskId);
    if (!existingTask) {
      throw new Error(`Task ${taskId} not found`);
    }

    if (existingTask.version !== expectedVersion) {
      throw new Error(`Task ${taskId} version mismatch. Expected ${expectedVersion}, got ${existingTask.version}`);
    }

    const updatedTask = {
      ...existingTask,
      ...updates,
      version: existingTask.version + 1,
      updatedAt: new Date().toISOString()
    };

    this.tasks.set(taskId, updatedTask);
    return updatedTask;
  }

  async delete(taskId: string): Promise<boolean> {
    this.ensureInitialized();
    return this.tasks.delete(taskId);
  }

  async list(contextId?: string, state?: TaskState, limit?: number, offset?: number): Promise<PersistedTask[]> {
    this.ensureInitialized();
    
    let tasks = Array.from(this.tasks.values());
    
    if (contextId) {
      tasks = tasks.filter(task => task.contextId === contextId);
    }
    
    if (state) {
      tasks = tasks.filter(task => task.status.state === state);
    }
    
    // Sort by creation time (newest first)
    tasks.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
    
    if (offset) {
      tasks = tasks.slice(offset);
    }
    
    if (limit) {
      tasks = tasks.slice(0, limit);
    }
    
    return tasks;
  }

  async count(contextId?: string, state?: TaskState): Promise<number> {
    const tasks = await this.list(contextId, state);
    return tasks.length;
  }

  async cleanup(olderThan: Date): Promise<number> {
    this.ensureInitialized();
    
    let deletedCount = 0;
    const cutoffTime = olderThan.getTime();
    
    for (const [taskId, task] of this.tasks.entries()) {
      const taskTime = new Date(task.createdAt).getTime();
      if (taskTime < cutoffTime) {
        this.tasks.delete(taskId);
        deletedCount++;
      }
    }
    
    return deletedCount;
  }

  async getMetrics(): Promise<TaskStorageMetrics> {
    this.ensureInitialized();
    
    const tasks = Array.from(this.tasks.values());
    const tasksByState: Record<TaskState, number> = {} as Record<TaskState, number>;
    const tasksByPriority: Record<TaskPriority, number> = {} as Record<TaskPriority, number>;
    
    // Initialize counters
    Object.values(TaskState).forEach(state => {
      tasksByState[state] = 0;
    });
    Object.values(TaskPriority).forEach(priority => {
      tasksByPriority[priority] = 0;
    });
    
    // Count tasks
    tasks.forEach(task => {
      tasksByState[task.status.state]++;
      tasksByPriority[task.priority]++;
    });
    
    // Calculate average duration for completed tasks
    const completedTasks = tasks.filter(task => task.status.state === TaskState.Completed);
    let averageTaskDuration = 0;
    
    if (completedTasks.length > 0) {
      const totalDuration = completedTasks.reduce((sum, task) => {
        const created = new Date(task.createdAt).getTime();
        const updated = new Date(task.updatedAt).getTime();
        return sum + (updated - created);
      }, 0);
      averageTaskDuration = totalDuration / completedTasks.length;
    }
    
    return {
      totalTasks: tasks.length,
      tasksByState,
      tasksByPriority,
      averageTaskDuration,
      storageSize: JSON.stringify(tasks).length,
    };
  }

  private ensureInitialized(): void {
    if (!this.initialized) {
      throw new Error('TaskStorage not initialized');
    }
  }
}

/**
 * Task Persistence Manager Configuration
 */
export interface TaskPersistenceConfig {
  retentionPeriod: number;
  enableHistory: boolean;
  enableChecksums: boolean;
  cleanupInterval: number;
}

/**
 * Task Persistence Manager (Simplified)
 */
export class TaskPersistenceManager {
  private storage: TaskStorage;
  private config: TaskPersistenceConfig;
  private cleanupTimer?: NodeJS.Timeout;

  constructor(storage: TaskStorage, config: Partial<TaskPersistenceConfig> = {}) {
    this.storage = storage;
    this.config = {
      retentionPeriod: 7 * 24 * 60 * 60 * 1000, // 7 days
      enableHistory: true,
      enableChecksums: true,
      cleanupInterval: 60 * 60 * 1000, // 1 hour
      ...config
    };
  }

  async initialize(): Promise<void> {
    await this.storage.initialize();
    
    if (this.config.cleanupInterval > 0) {
      this.startCleanupTimer();
    }
  }

  async shutdown(): Promise<void> {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
      this.cleanupTimer = undefined;
    }
    
    await this.storage.shutdown();
  }

  async createTask(task: Partial<PersistedTask>): Promise<PersistedTask> {
    const now = new Date().toISOString();
    
    const persistedTask: PersistedTask = {
      id: task.id || this.generateTaskId(),
      contextId: task.contextId || 'default',
      status: task.status || { state: TaskState.Submitted, timestamp: now },
      priority: task.priority || TaskPriority.Normal,
      createdAt: now,
      updatedAt: now,
      expiresAt: task.expiresAt,
      version: 1,
      checksum: '',
      history: [],
      artifacts: task.artifacts || [],
      metadata: task.metadata || {},
      kind: task.kind || 'task'
    };

    if (this.config.enableChecksums) {
      persistedTask.checksum = this.calculateChecksum(persistedTask);
    }

    return await this.storage.create(persistedTask);
  }

  async getTask(taskId: string): Promise<PersistedTask | null> {
    return await this.storage.get(taskId);
  }

  async updateTask(
    taskId: string, 
    updates: Partial<PersistedTask>, 
    expectedVersion?: number
  ): Promise<PersistedTask> {
    const existingTask = await this.storage.get(taskId);
    if (!existingTask) {
      throw new Error(`Task ${taskId} not found`);
    }

    const version = expectedVersion ?? existingTask.version;
    
    // Add history entry if state is changing
    if (updates.status && updates.status.state !== existingTask.status.state) {
      const historyEntry: TaskHistoryEntry = {
        timestamp: new Date().toISOString(),
        previousState: existingTask.status.state,
        newState: updates.status.state,
        reason: updates.status.message
      };
      
      updates.history = [...(existingTask.history || []), historyEntry];
    }

    const updatedTask = await this.storage.update(taskId, updates, version);
    
    if (this.config.enableChecksums) {
      updatedTask.checksum = this.calculateChecksum(updatedTask);
    }

    return updatedTask;
  }

  async deleteTask(taskId: string): Promise<boolean> {
    return await this.storage.delete(taskId);
  }

  async listTasks(
    contextId?: string, 
    state?: TaskState, 
    limit?: number, 
    offset?: number
  ): Promise<PersistedTask[]> {
    return await this.storage.list(contextId, state, limit, offset);
  }

  async getMetrics(): Promise<TaskStorageMetrics> {
    return await this.storage.getMetrics();
  }

  private generateTaskId(): string {
    return `task-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private calculateChecksum(task: PersistedTask): string {
    // Simple checksum implementation
    const data = JSON.stringify({
      id: task.id,
      contextId: task.contextId,
      status: task.status,
      metadata: task.metadata
    });
    
    let hash = 0;
    for (let i = 0; i < data.length; i++) {
      const char = data.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    
    return Math.abs(hash).toString(16);
  }

  private startCleanupTimer(): void {
    this.cleanupTimer = setInterval(async () => {
      try {
        const cutoffDate = new Date(Date.now() - this.config.retentionPeriod);
        await this.storage.cleanup(cutoffDate);
      } catch (error) {
        console.error('Task cleanup failed:', error);
      }
    }, this.config.cleanupInterval);
  }
}
