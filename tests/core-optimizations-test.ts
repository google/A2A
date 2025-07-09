/**
 * Core Optimizations Test - Minimal Dependencies
 *
 * This test file validates only the core optimization components
 * without requiring the full production implementation.
 */

// Simple test framework
interface TestResult {
  name: string;
  passed: boolean;
  error?: string;
}

class CoreTestRunner {
  private results: TestResult[] = [];

  async test(name: string, testFn: () => Promise<void> | void): Promise<void> {
    try {
      await testFn();
      this.results.push({ name, passed: true });
      console.log(`✅ ${name}`);
    } catch (error) {
      this.results.push({
        name,
        passed: false,
        error: error instanceof Error ? error.message : String(error),
      });
      console.log(`❌ ${name}: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  getSummary(): { total: number; passed: number; failed: number } {
    const total = this.results.length;
    const passed = this.results.filter(r => r.passed).length;
    return { total, passed, failed: total - passed };
  }
}

// Import only core optimization components
import {
  A2AErrorHandler,
  A2AErrorCode,
  A2AError,
} from '../types/src/error-handling';

import {
  TaskPersistenceManager,
  MemoryTaskStorage,
  TaskState,
} from '../types/src/task-persistence';

import {
  A2AConnectionPool,
  ConnectionState,
} from '../types/src/connection-pool';

// Test utilities
function createTestTask(id: string = 'test-task'): Partial<PersistedTask> {
  return {
    id,
    contextId: 'test-context',
    status: {
      state: TaskState.Submitted,
      timestamp: new Date().toISOString(),
    },
    history: [],
    artifacts: [],
    kind: 'task',
  };
}

function createMockConnection(agentUrl: string): A2AConnection {
  return {
    info: {
      id: `mock-${Date.now()}`,
      state: ConnectionState.IDLE,
      createdAt: Date.now(),
      lastUsedAt: Date.now(),
      useCount: 0,
      agentUrl,
      metadata: {},
    },
    sendRequest: async () => ({ result: 'mock-response' }),
    isHealthy: async () => true,
    close: async () => { },
    reset: async () => { },
  };
}

// Main test function
async function runCoreOptimizationTests(): Promise<void> {
  const runner = new CoreTestRunner();

  console.log('🧪 Testing Core A2A Optimizations...\n');

  // Test 1: Error Handler Basic Functionality
  await runner.test('Error Handler - Creation and Configuration', async () => {
    const errorHandler = new A2AErrorHandler({
      maxRetries: 3,
      baseDelay: 100,
      maxDelay: 1000,
    });

    const status = errorHandler.getCircuitBreakerStatus();
    if (status.state !== 'closed') {
      throw new Error('Circuit breaker should start in closed state');
    }
  });

  // Test 2: Error Handler Retry Logic
  await runner.test('Error Handler - Retry Mechanism', async () => {
    const errorHandler = new A2AErrorHandler({
      maxRetries: 2,
      baseDelay: 10,
      maxDelay: 100,
    });

    let attemptCount = 0;
    const operation = async () => {
      attemptCount++;
      if (attemptCount < 3) {
        throw new A2AError({
          code: A2AErrorCode.NETWORK_TIMEOUT,
          message: 'Network timeout',
        });
      }
      return 'success';
    };

    const result = await errorHandler.executeWithRetry(operation);
    if (result !== 'success' || attemptCount !== 3) {
      throw new Error(`Expected 3 attempts and success, got ${attemptCount} attempts`);
    }
  });

  // Test 3: Task Persistence Basic Operations
  await runner.test('Task Persistence - CRUD Operations', async () => {
    const storage = new MemoryTaskStorage();
    const taskManager = new TaskPersistenceManager(storage, {
      retentionPeriod: 60000,
      enableHistory: true,
    });

    await taskManager.initialize();

    const task = createTestTask('test-task-001');
    const persistedTask = await taskManager.createTask(task);

    if (persistedTask.id !== task.id || persistedTask.version !== 1) {
      throw new Error('Task creation failed');
    }

    const retrievedTask = await taskManager.getTask(task.id);
    if (!retrievedTask || retrievedTask.id !== task.id) {
      throw new Error('Task retrieval failed');
    }

    await taskManager.shutdown();
  });

  // Test 4: Task Persistence Optimistic Locking
  await runner.test('Task Persistence - Version Control', async () => {
    const storage = new MemoryTaskStorage();
    const taskManager = new TaskPersistenceManager(storage, {
      retentionPeriod: 60000,
      enableHistory: true,
    });

    await taskManager.initialize();

    const task = createTestTask('test-task-002');
    const persistedTask = await taskManager.createTask(task);

    // Update with correct version
    const updatedTask = await taskManager.updateTask(
      task.id,
      { status: { state: TaskState.Working, timestamp: new Date().toISOString() } },
      persistedTask.version
    );

    if (updatedTask.version !== 2) {
      throw new Error('Version should increment after update');
    }

    // Try to update with wrong version (should fail)
    try {
      await taskManager.updateTask(
        task.id,
        { status: { state: TaskState.Completed, timestamp: new Date().toISOString() } },
        1 // Wrong version
      );
      throw new Error('Should have thrown version mismatch error');
    } catch (error) {
      if (!error.message.includes('version mismatch')) {
        throw new Error('Expected version mismatch error');
      }
    }

    await taskManager.shutdown();
  });

  // Test 5: Connection Pool Basic Operations
  await runner.test('Connection Pool - Basic Functionality', async () => {
    const mockFactory = {
      createConnection: async (agentUrl: string) => createMockConnection(agentUrl),
      validateConnection: async () => true,
    };

    const pool = new A2AConnectionPool(mockFactory, {
      minConnections: 1,
      maxConnections: 5,
      acquireTimeout: 5000,
      healthCheckInterval: 0,
    });

    const agentUrl = 'https://test-agent.example.com';
    const connection = await pool.acquireConnection(agentUrl);

    if (!connection || connection.info.state !== ConnectionState.ACTIVE) {
      throw new Error('Connection acquisition failed');
    }

    await pool.releaseConnection(connection);

    if (connection.info.state !== ConnectionState.IDLE) {
      throw new Error('Connection release failed');
    }

    await pool.shutdown();
  });

  // Test 6: Connection Pool Metrics
  await runner.test('Connection Pool - Metrics Collection', async () => {
    const mockFactory = {
      createConnection: async (agentUrl: string) => createMockConnection(agentUrl),
      validateConnection: async () => true,
    };

    const pool = new A2AConnectionPool(mockFactory, {
      minConnections: 1,
      maxConnections: 5,
      enableMetrics: true,
    });

    const agentUrl = 'https://test-agent.example.com';
    await pool.executeRequest(agentUrl, 'test-method', {});

    const metrics = pool.getMetrics();
    if (metrics.totalConnections === 0 || metrics.totalRequests === 0) {
      throw new Error('Metrics not being collected properly');
    }

    await pool.shutdown();
  });

  // Test 7: Integration Test
  await runner.test('Integration - Error Handler + Task Persistence', async () => {
    const errorHandler = new A2AErrorHandler();
    const storage = new MemoryTaskStorage();
    const taskManager = new TaskPersistenceManager(storage);

    await taskManager.initialize();

    const result = await errorHandler.executeWithRetry(async () => {
      const task = createTestTask('integration-test');
      return await taskManager.createTask(task);
    });

    if (!result || result.id !== 'integration-test') {
      throw new Error('Integration test failed');
    }

    await taskManager.shutdown();
  });

  // Print results
  console.log('\n📊 Core Optimization Test Results:');
  const summary = runner.getSummary();
  console.log(`Total: ${summary.total}, Passed: ${summary.passed}, Failed: ${summary.failed}`);

  if (summary.failed > 0) {
    console.log('\n❌ Some tests failed');
    throw new Error(`${summary.failed} tests failed`);
  } else {
    console.log('\n✅ All core optimization tests passed!');
  }
}

// Run tests if this file is executed directly
if (require.main === module) {
  runCoreOptimizationTests().catch(error => {
    console.error('❌ Core optimization tests failed:', error);
    throw error;
  });
}

export { runCoreOptimizationTests, CoreTestRunner };
