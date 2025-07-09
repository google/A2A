/**
 * High-Performance Connection Pool and Resource Management for A2A Protocol (KISS Version)
 *
 * This module provides efficient connection pooling with connection reuse,
 * resource management, and backpressure handling for A2A client-server
 * communications following KISS principles.
 */

/**
 * Connection States
 */
export enum ConnectionState {
  IDLE = 'idle',
  ACTIVE = 'active',
  BUSY = 'busy',
  ERROR = 'error',
  CLOSED = 'closed'
}

/**
 * Connection Information
 */
export interface ConnectionInfo {
  id: string;
  state: ConnectionState;
  createdAt: number;
  lastUsedAt: number;
  useCount: number;
  agentUrl: string;
  metadata: Record<string, any>;
}

/**
 * A2A Connection Interface
 */
export interface A2AConnection {
  info: ConnectionInfo;
  sendRequest(method: string, params: any): Promise<any>;
  isHealthy(): Promise<boolean>;
  close(): Promise<void>;
  reset(): Promise<void>;
}

/**
 * Connection Factory Interface
 */
export interface ConnectionFactory {
  createConnection(agentUrl: string): Promise<A2AConnection>;
  validateConnection(connection: A2AConnection): Promise<boolean>;
}

/**
 * HTTP Connection Factory Implementation (Primary Protocol)
 */
export class HTTPConnectionFactory implements ConnectionFactory {
  async createConnection(agentUrl: string): Promise<A2AConnection> {
    const connectionId = `http-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    return {
      info: {
        id: connectionId,
        state: ConnectionState.IDLE,
        createdAt: Date.now(),
        lastUsedAt: Date.now(),
        useCount: 0,
        agentUrl,
        metadata: { protocol: 'http' }
      },

      async sendRequest(method: string, params: any): Promise<any> {
        this.info.state = ConnectionState.ACTIVE;
        this.info.lastUsedAt = Date.now();
        this.info.useCount++;

        try {
          // HTTP request implementation
          const response = await fetch(agentUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ method, params, id: Date.now() })
          });

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }

          const result = await response.json();
          this.info.state = ConnectionState.IDLE;
          return result;
        } catch (error) {
          this.info.state = ConnectionState.ERROR;
          throw error;
        }
      },

      async isHealthy(): Promise<boolean> {
        try {
          await this.sendRequest('ping', {});
          return true;
        } catch {
          return false;
        }
      },

      async close(): Promise<void> {
        this.info.state = ConnectionState.CLOSED;
      },

      async reset(): Promise<void> {
        this.info.state = ConnectionState.IDLE;
        this.info.useCount = 0;
        this.info.lastUsedAt = Date.now();
      }
    };
  }

  async validateConnection(connection: A2AConnection): Promise<boolean> {
    return connection.info.state !== ConnectionState.CLOSED &&
      connection.info.state !== ConnectionState.ERROR;
  }
}

/**
 * Connection Pool Configuration
 */
export interface ConnectionPoolConfig {
  minConnections: number;
  maxConnections: number;
  acquireTimeout: number;
  idleTimeout: number;
  maxLifetime: number;
  healthCheckInterval: number;
  cleanupInterval: number;
  enableMetrics: boolean;
}

/**
 * Connection Pool Metrics
 */
export interface ConnectionPoolMetrics {
  totalConnections: number;
  activeConnections: number;
  idleConnections: number;
  queuedRequests: number;
  totalRequests: number;
  failedRequests: number;
  averageResponseTime: number;
  connectionUtilization: number;
}

/**
 * High-Performance A2A Connection Pool (Simplified)
 */
export class A2AConnectionPool {
  private factory: ConnectionFactory;
  private config: ConnectionPoolConfig;
  private connections: Map<string, A2AConnection[]> = new Map();
  private requestQueue: Array<{
    agentUrl: string;
    resolve: (connection: A2AConnection) => void;
    reject: (error: Error) => void;
    timestamp: number;
  }> = [];

  private metrics: ConnectionPoolMetrics = {
    totalConnections: 0,
    activeConnections: 0,
    idleConnections: 0,
    queuedRequests: 0,
    totalRequests: 0,
    failedRequests: 0,
    averageResponseTime: 0,
    connectionUtilization: 0
  };

  private healthCheckTimer?: NodeJS.Timeout;
  private cleanupTimer?: NodeJS.Timeout;

  constructor(factory: ConnectionFactory, config: Partial<ConnectionPoolConfig> = {}) {
    this.factory = factory;
    this.config = {
      minConnections: 2,
      maxConnections: 10,
      acquireTimeout: 30000,
      idleTimeout: 300000,
      maxLifetime: 3600000,
      healthCheckInterval: 60000,
      cleanupInterval: 60000,
      enableMetrics: true,
      ...config
    };

    if (this.config.healthCheckInterval > 0) {
      this.startHealthCheck();
    }

    if (this.config.cleanupInterval > 0) {
      this.startCleanup();
    }
  }

  async acquireConnection(agentUrl: string): Promise<A2AConnection> {
    const startTime = Date.now();

    try {
      // Try to get an existing idle connection
      const connection = await this.getIdleConnection(agentUrl);
      if (connection) {
        connection.info.state = ConnectionState.ACTIVE;
        this.updateMetrics();
        return connection;
      }

      // Create new connection if under limit
      if (this.getTotalConnections() < this.config.maxConnections) {
        const newConnection = await this.createConnection(agentUrl);
        newConnection.info.state = ConnectionState.ACTIVE;
        this.updateMetrics();
        return newConnection;
      }

      // Queue the request
      return await this.queueRequest(agentUrl);
    } finally {
      if (this.config.enableMetrics) {
        this.metrics.totalRequests++;
        const responseTime = Date.now() - startTime;
        this.metrics.averageResponseTime =
          (this.metrics.averageResponseTime * (this.metrics.totalRequests - 1) + responseTime) /
          this.metrics.totalRequests;
      }
    }
  }

  async releaseConnection(connection: A2AConnection): Promise<void> {
    // Only set to IDLE if connection is not in ERROR state
    if (connection.info.state !== ConnectionState.ERROR) {
      connection.info.state = ConnectionState.IDLE;
    }
    connection.info.lastUsedAt = Date.now();

    // Process queued requests (important for both success and error cases)
    await this.processQueue();
    this.updateMetrics();
  }

  async executeRequest(agentUrl: string, method: string, params: any): Promise<any> {
    const connection = await this.acquireConnection(agentUrl);

    try {
      const result = await connection.sendRequest(method, params);
      await this.releaseConnection(connection);
      return result;
    } catch (error) {
      // Mark connection as error state
      connection.info.state = ConnectionState.ERROR;

      // Update metrics
      if (this.config.enableMetrics) {
        this.metrics.failedRequests++;
      }

      // Critical: Release the connection back to pool and process queue
      // This prevents connection leaks and ensures waiting requests are processed
      try {
        await this.releaseConnection(connection);
      } catch (releaseError) {
        // Log release error but don't throw to avoid masking original error
        console.error('Failed to release connection after error:', releaseError);
      }

      throw error;
    }
  }

  getMetrics(): ConnectionPoolMetrics {
    this.updateMetrics();
    return { ...this.metrics };
  }

  async shutdown(): Promise<void> {
    if (this.healthCheckTimer) {
      clearInterval(this.healthCheckTimer);
    }

    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
    }

    // Close all connections
    for (const connections of this.connections.values()) {
      for (const connection of connections) {
        await connection.close();
      }
    }

    this.connections.clear();
    this.requestQueue.length = 0;
  }

  private async getIdleConnection(agentUrl: string): Promise<A2AConnection | null> {
    const connections = this.connections.get(agentUrl) || [];

    for (const connection of connections) {
      if (connection.info.state === ConnectionState.IDLE) {
        const isValid = await this.factory.validateConnection(connection);
        if (isValid) {
          return connection;
        } else {
          await this.removeConnection(agentUrl, connection);
        }
      }
    }

    return null;
  }

  private async createConnection(agentUrl: string): Promise<A2AConnection> {
    const connection = await this.factory.createConnection(agentUrl);

    if (!this.connections.has(agentUrl)) {
      this.connections.set(agentUrl, []);
    }

    this.connections.get(agentUrl)!.push(connection);
    this.metrics.totalConnections++;

    return connection;
  }

  private async queueRequest(agentUrl: string): Promise<A2AConnection> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        const index = this.requestQueue.findIndex(req => req.resolve === resolve);
        if (index >= 0) {
          this.requestQueue.splice(index, 1);
          this.metrics.queuedRequests--;
        }
        reject(new Error('Connection acquire timeout'));
      }, this.config.acquireTimeout);

      this.requestQueue.push({
        agentUrl,
        resolve: (connection) => {
          clearTimeout(timeout);
          resolve(connection);
        },
        reject: (error) => {
          clearTimeout(timeout);
          reject(error);
        },
        timestamp: Date.now()
      });

      this.metrics.queuedRequests++;
    });
  }

  private async processQueue(): Promise<void> {
    while (this.requestQueue.length > 0) {
      const request = this.requestQueue[0];

      // Clean up any ERROR state connections for this agent before processing queue
      await this.cleanupErrorConnections(request.agentUrl);

      const connection = await this.getIdleConnection(request.agentUrl);

      if (connection) {
        this.requestQueue.shift();
        this.metrics.queuedRequests--;
        connection.info.state = ConnectionState.ACTIVE;
        request.resolve(connection);
      } else {
        break;
      }
    }
  }

  /**
   * Clean up connections in ERROR state to prevent connection leaks
   */
  private async cleanupErrorConnections(agentUrl: string): Promise<void> {
    const connections = this.connections.get(agentUrl);
    if (!connections) return;

    const errorConnections = connections.filter(conn => conn.info.state === ConnectionState.ERROR);

    for (const errorConnection of errorConnections) {
      await this.removeConnection(agentUrl, errorConnection);
    }
  }

  private async removeConnection(agentUrl: string, connection: A2AConnection): Promise<void> {
    const connections = this.connections.get(agentUrl);
    if (connections) {
      const index = connections.indexOf(connection);
      if (index >= 0) {
        connections.splice(index, 1);
        this.metrics.totalConnections--;
        await connection.close();
      }
    }
  }

  private getTotalConnections(): number {
    // Use existing metric instead of iterating through all connections
    // This is more efficient and avoids redundant calculations
    return this.metrics.totalConnections;
  }

  private updateMetrics(): void {
    if (!this.config.enableMetrics) return;

    let active = 0;
    let idle = 0;

    for (const connections of this.connections.values()) {
      for (const connection of connections) {
        if (connection.info.state === ConnectionState.ACTIVE) {
          active++;
        } else if (connection.info.state === ConnectionState.IDLE) {
          idle++;
        }
      }
    }

    this.metrics.activeConnections = active;
    this.metrics.idleConnections = idle;
    this.metrics.connectionUtilization =
      this.metrics.totalConnections > 0 ? active / this.metrics.totalConnections : 0;
  }

  private startHealthCheck(): void {
    this.healthCheckTimer = setInterval(async () => {
      for (const [agentUrl, connections] of this.connections.entries()) {
        for (const connection of [...connections]) {
          if (connection.info.state === ConnectionState.IDLE) {
            const isHealthy = await connection.isHealthy();
            if (!isHealthy) {
              await this.removeConnection(agentUrl, connection);
            }
          }
        }
      }
    }, this.config.healthCheckInterval);
  }

  private startCleanup(): void {
    this.cleanupTimer = setInterval(async () => {
      const now = Date.now();

      for (const [agentUrl, connections] of this.connections.entries()) {
        for (const connection of [...connections]) {
          const age = now - connection.info.createdAt;
          const idleTime = now - connection.info.lastUsedAt;

          if (age > this.config.maxLifetime ||
            (connection.info.state === ConnectionState.IDLE && idleTime > this.config.idleTimeout)) {
            await this.removeConnection(agentUrl, connection);
          }
        }
      }
    }, this.config.cleanupInterval); // Use configurable cleanup interval
  }
}
