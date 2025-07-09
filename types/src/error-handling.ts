/**
 * Enhanced Error Handling and Retry Mechanism for A2A Protocol
 *
 * This module provides comprehensive error handling, retry logic with exponential backoff,
 * circuit breaker pattern, and correlation tracking for distributed systems.
 *
 * Key Features:
 * - Standardized A2A error codes and classification
 * - Exponential backoff retry with jitter
 * - Circuit breaker pattern for failure protection
 * - Correlation tracking for distributed tracing
 * - Structured error reporting and categorization
 */

import { JSONRPCError } from './types';

/**
 * Standardized A2A Error Codes
 * Provides consistent error classification across the A2A ecosystem
 */
export enum A2AErrorCode {
  // Network and Connection Errors (1000-1099)
  NETWORK_TIMEOUT = 1001,
  CONNECTION_FAILED = 1002,
  CONNECTION_REFUSED = 1003,
  DNS_RESOLUTION_FAILED = 1004,
  SSL_HANDSHAKE_FAILED = 1005,

  // Protocol and Communication Errors (1100-1199)
  PROTOCOL_VERSION_MISMATCH = 1101,
  INVALID_MESSAGE_FORMAT = 1102,
  MESSAGE_TOO_LARGE = 1103,
  COMPRESSION_ERROR = 1104,
  ENCODING_ERROR = 1105,

  // Authentication and Authorization Errors (1200-1299)
  AUTHENTICATION_FAILED = 1201,
  AUTHORIZATION_DENIED = 1202,
  TOKEN_EXPIRED = 1203,
  TOKEN_INVALID = 1204,
  INSUFFICIENT_PERMISSIONS = 1205,

  // Agent and Service Errors (1300-1399)
  AGENT_UNAVAILABLE = 1301,
  AGENT_OVERLOADED = 1302,
  AGENT_MAINTENANCE = 1303,
  SERVICE_UNAVAILABLE = 1304,
  SERVICE_DEGRADED = 1305,

  // Task and Execution Errors (1400-1499)
  TASK_TIMEOUT = 1401,
  TASK_CANCELLED = 1402,
  TASK_FAILED = 1403,
  RESOURCE_EXHAUSTED = 1404,
  QUOTA_EXCEEDED = 1405,

  // Data and Validation Errors (1500-1599)
  INVALID_INPUT = 1501,
  VALIDATION_FAILED = 1502,
  SCHEMA_MISMATCH = 1503,
  DATA_CORRUPTION = 1504,
  SERIALIZATION_ERROR = 1505,

  // JSON-RPC Standard Errors (-32xxx)
  PARSE_ERROR = -32700,
  INVALID_REQUEST = -32600,
  METHOD_NOT_FOUND = -32601,
  INVALID_PARAMS = -32602,
  INTERNAL_ERROR = -32603,

  // Generic Errors
  UNKNOWN_ERROR = 9999
}

/**
 * Error Categories for Classification
 */
export enum ErrorCategory {
  NETWORK = 'network',
  PROTOCOL = 'protocol',
  AUTHENTICATION = 'authentication',
  AGENT = 'agent',
  TASK = 'task',
  DATA = 'data',
  SYSTEM = 'system'
}

/**
 * Error Severity Levels
 */
export enum ErrorSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

/**
 * Enhanced A2A Error with Rich Context
 */
export class A2AError extends Error {
  public readonly code: A2AErrorCode;
  public readonly category: ErrorCategory;
  public readonly severity: ErrorSeverity;
  public readonly correlationId?: string;
  public readonly timestamp: string;
  public readonly context: Record<string, any>;
  public readonly retryable: boolean;
  public readonly cause?: Error;

  constructor(options: {
    code: A2AErrorCode;
    message: string;
    category?: ErrorCategory;
    severity?: ErrorSeverity;
    correlationId?: string;
    context?: Record<string, any>;
    retryable?: boolean;
    cause?: Error;
  }) {
    super(options.message);
    this.name = 'A2AError';
    this.code = options.code;
    this.category = options.category || this.inferCategory(options.code);
    this.severity = options.severity || this.inferSeverity(options.code);
    this.correlationId = options.correlationId;
    this.timestamp = new Date().toISOString();
    this.context = options.context || {};
    this.retryable = options.retryable ?? this.inferRetryable(options.code);
    this.cause = options.cause;

    // Maintain proper stack trace
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, A2AError);
    }
  }

  private inferCategory(code: A2AErrorCode): ErrorCategory {
    if (code >= 1000 && code < 1100) return ErrorCategory.NETWORK;
    if (code >= 1100 && code < 1200) return ErrorCategory.PROTOCOL;
    if (code >= 1200 && code < 1300) return ErrorCategory.AUTHENTICATION;
    if (code >= 1300 && code < 1400) return ErrorCategory.AGENT;
    if (code >= 1400 && code < 1500) return ErrorCategory.TASK;
    if (code >= 1500 && code < 1600) return ErrorCategory.DATA;
    return ErrorCategory.SYSTEM;
  }

  private inferSeverity(code: A2AErrorCode): ErrorSeverity {
    const criticalCodes = [
      A2AErrorCode.DATA_CORRUPTION,
      A2AErrorCode.INTERNAL_ERROR,
      A2AErrorCode.RESOURCE_EXHAUSTED
    ];

    const highCodes = [
      A2AErrorCode.AUTHENTICATION_FAILED,
      A2AErrorCode.AUTHORIZATION_DENIED,
      A2AErrorCode.SERVICE_UNAVAILABLE
    ];

    if (criticalCodes.includes(code)) return ErrorSeverity.CRITICAL;
    if (highCodes.includes(code)) return ErrorSeverity.HIGH;
    if (code >= 1000 && code < 1500) return ErrorSeverity.MEDIUM;
    return ErrorSeverity.LOW;
  }

  private inferRetryable(code: A2AErrorCode): boolean {
    const nonRetryableCodes = [
      A2AErrorCode.AUTHENTICATION_FAILED,
      A2AErrorCode.AUTHORIZATION_DENIED,
      A2AErrorCode.INVALID_INPUT,
      A2AErrorCode.VALIDATION_FAILED,
      A2AErrorCode.PARSE_ERROR,
      A2AErrorCode.INVALID_REQUEST,
      A2AErrorCode.METHOD_NOT_FOUND,
      A2AErrorCode.INVALID_PARAMS
    ];

    return !nonRetryableCodes.includes(code);
  }

  /**
   * Convert to JSON-RPC Error format
   */
  toJSONRPCError(): JSONRPCError {
    return {
      code: this.code,
      message: this.message,
      data: {
        category: this.category,
        severity: this.severity,
        correlationId: this.correlationId,
        timestamp: this.timestamp,
        context: this.context,
        retryable: this.retryable
      }
    };
  }

  /**
   * Create error from JSON-RPC Error
   */
  static fromJSONRPCError(error: JSONRPCError, correlationId?: string): A2AError {
    return new A2AError({
      code: error.code as A2AErrorCode,
      message: error.message,
      category: error.data?.category,
      severity: error.data?.severity,
      correlationId: correlationId || error.data?.correlationId,
      context: error.data?.context,
      retryable: error.data?.retryable
    });
  }
}

/**
 * Circuit Breaker States
 */
export enum CircuitBreakerState {
  CLOSED = 'closed',
  OPEN = 'open',
  HALF_OPEN = 'half_open'
}

/**
 * Circuit Breaker Configuration
 */
export interface CircuitBreakerConfig {
  failureThreshold: number;
  recoveryTimeout: number;
  monitoringPeriod: number;
  halfOpenMaxCalls: number;
}

/**
 * Retry Configuration
 */
export interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
  jitterFactor: number;
}

/**
 * Error Handler Configuration
 */
export interface ErrorHandlerConfig {
  retryConfig?: Partial<RetryConfig>;
  circuitBreakerConfig?: Partial<CircuitBreakerConfig>;
  enableCorrelationTracking?: boolean;
  enableMetrics?: boolean;
}

/**
 * Circuit Breaker Status
 */
export interface CircuitBreakerStatus {
  state: CircuitBreakerState;
  failureCount: number;
  lastFailureTime?: number;
  nextRetryTime?: number;
}

/**
 * Error Handler Metrics
 */
export interface ErrorHandlerMetrics {
  totalErrors: number;
  retriedErrors: number;
  circuitBreakerTrips: number;
  averageRetryDelay: number;
  errorsByCategory: Record<ErrorCategory, number>;
  errorsBySeverity: Record<ErrorSeverity, number>;
}

/**
 * Enhanced A2A Error Handler with Circuit Breaker and Retry Logic
 */
export class A2AErrorHandler {
  private readonly retryConfig: RetryConfig;
  private readonly circuitBreakerConfig: CircuitBreakerConfig;
  private readonly enableCorrelationTracking: boolean;
  private readonly enableMetrics: boolean;

  private circuitBreakerState: CircuitBreakerState = CircuitBreakerState.CLOSED;
  private failureCount: number = 0;
  private lastFailureTime?: number;
  private halfOpenCalls: number = 0;

  private metrics: ErrorHandlerMetrics = {
    totalErrors: 0,
    retriedErrors: 0,
    circuitBreakerTrips: 0,
    averageRetryDelay: 0,
    errorsByCategory: {} as Record<ErrorCategory, number>,
    errorsBySeverity: {} as Record<ErrorSeverity, number>
  };

  constructor(config: ErrorHandlerConfig = {}) {
    this.retryConfig = {
      maxRetries: 3,
      baseDelay: 1000,
      maxDelay: 30000,
      backoffMultiplier: 2,
      jitterFactor: 0.1,
      ...config.retryConfig
    };

    this.circuitBreakerConfig = {
      failureThreshold: 5,
      recoveryTimeout: 60000,
      monitoringPeriod: 10000,
      halfOpenMaxCalls: 3,
      ...config.circuitBreakerConfig
    };

    this.enableCorrelationTracking = config.enableCorrelationTracking ?? true;
    this.enableMetrics = config.enableMetrics ?? true;

    // Initialize metrics categories
    Object.values(ErrorCategory).forEach(category => {
      this.metrics.errorsByCategory[category] = 0;
    });
    Object.values(ErrorSeverity).forEach(severity => {
      this.metrics.errorsBySeverity[severity] = 0;
    });
  }

  /**
   * Execute operation with retry and circuit breaker protection
   */
  async executeWithRetry<T>(
    operation: () => Promise<T>,
    correlationId?: string
  ): Promise<T> {
    const operationId = correlationId || this.generateCorrelationId();

    // Check circuit breaker
    if (!this.canExecute()) {
      throw new A2AError({
        code: A2AErrorCode.SERVICE_UNAVAILABLE,
        message: 'Circuit breaker is open',
        correlationId: operationId,
        context: { circuitBreakerState: this.circuitBreakerState }
      });
    }

    let lastError: A2AError | undefined;
    let attempt = 0;

    while (attempt <= this.retryConfig.maxRetries) {
      try {
        const result = await operation();

        // Success - reset circuit breaker if needed
        if (this.circuitBreakerState === CircuitBreakerState.HALF_OPEN) {
          this.halfOpenCalls++;
          if (this.halfOpenCalls >= this.circuitBreakerConfig.halfOpenMaxCalls) {
            this.resetCircuitBreaker();
          }
        }

        return result;
      } catch (error) {
        const a2aError = this.normalizeError(error, operationId);
        lastError = a2aError;

        this.recordError(a2aError);

        // Check if error is retryable
        if (!a2aError.retryable || attempt >= this.retryConfig.maxRetries) {
          this.handleFailure();
          throw a2aError;
        }

        // Calculate delay with exponential backoff and jitter
        const delay = this.calculateDelay(attempt);
        await this.sleep(delay);

        attempt++;
        this.metrics.retriedErrors++;
      }
    }

    // This should never be reached, but TypeScript requires it
    this.handleFailure();
    throw lastError!;
  }

  /**
   * Check if circuit breaker allows execution
   */
  private canExecute(): boolean {
    const now = Date.now();

    switch (this.circuitBreakerState) {
      case CircuitBreakerState.CLOSED:
        return true;

      case CircuitBreakerState.OPEN:
        if (this.lastFailureTime &&
          now - this.lastFailureTime >= this.circuitBreakerConfig.recoveryTimeout) {
          this.circuitBreakerState = CircuitBreakerState.HALF_OPEN;
          this.halfOpenCalls = 0;
          return true;
        }
        return false;

      case CircuitBreakerState.HALF_OPEN:
        return this.halfOpenCalls < this.circuitBreakerConfig.halfOpenMaxCalls;

      default:
        return false;
    }
  }

  /**
   * Handle operation failure
   */
  private handleFailure(): void {
    this.failureCount++;
    this.lastFailureTime = Date.now();

    if (this.circuitBreakerState === CircuitBreakerState.HALF_OPEN) {
      this.openCircuitBreaker();
    } else if (this.failureCount >= this.circuitBreakerConfig.failureThreshold) {
      this.openCircuitBreaker();
    }
  }

  /**
   * Open circuit breaker
   */
  private openCircuitBreaker(): void {
    this.circuitBreakerState = CircuitBreakerState.OPEN;
    this.metrics.circuitBreakerTrips++;
  }

  /**
   * Reset circuit breaker
   */
  private resetCircuitBreaker(): void {
    this.circuitBreakerState = CircuitBreakerState.CLOSED;
    this.failureCount = 0;
    this.halfOpenCalls = 0;
    this.lastFailureTime = undefined;
  }

  /**
   * Calculate retry delay with exponential backoff and jitter
   */
  private calculateDelay(attempt: number): number {
    const exponentialDelay = this.retryConfig.baseDelay *
      Math.pow(this.retryConfig.backoffMultiplier, attempt);

    const cappedDelay = Math.min(exponentialDelay, this.retryConfig.maxDelay);

    // Add jitter to prevent thundering herd
    const jitter = cappedDelay * this.retryConfig.jitterFactor * Math.random();

    return Math.floor(cappedDelay + jitter);
  }

  /**
   * Normalize any error to A2AError
   */
  private normalizeError(error: any, correlationId: string): A2AError {
    if (error instanceof A2AError) {
      return error;
    }

    // Map common error types to A2A error codes
    let code = A2AErrorCode.UNKNOWN_ERROR;

    if ([A2AErrorCode.NETWORK_TIMEOUT, A2AErrorCode.CONNECTION_FAILED,
    A2AErrorCode.SERVICE_UNAVAILABLE].includes(code)) {
      code = A2AErrorCode.NETWORK_TIMEOUT;
    }

    if ([A2AErrorCode.PARSE_ERROR, A2AErrorCode.INVALID_REQUEST,
    A2AErrorCode.METHOD_NOT_FOUND, A2AErrorCode.INVALID_PARAMS].includes(code)) {
      code = A2AErrorCode.INVALID_REQUEST;
    }

    return new A2AError({
      code,
      message: error.message || 'Unknown error occurred',
      correlationId,
      context: { originalError: error.name || 'Error' },
      cause: error instanceof Error ? error : undefined
    });
  }

  /**
   * Record error metrics
   */
  private recordError(error: A2AError): void {
    if (!this.enableMetrics) return;

    this.metrics.totalErrors++;
    this.metrics.errorsByCategory[error.category]++;
    this.metrics.errorsBySeverity[error.severity]++;
  }

  /**
   * Generate correlation ID for tracking
   */
  private generateCorrelationId(): string {
    if (!this.enableCorrelationTracking) return '';

    return `a2a-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Sleep utility
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Get circuit breaker status
   */
  getCircuitBreakerStatus(): CircuitBreakerStatus {
    return {
      state: this.circuitBreakerState,
      failureCount: this.failureCount,
      lastFailureTime: this.lastFailureTime,
      nextRetryTime: this.lastFailureTime ?
        this.lastFailureTime + this.circuitBreakerConfig.recoveryTimeout : undefined
    };
  }

  /**
   * Get error handler metrics
   */
  getMetrics(): ErrorHandlerMetrics {
    return { ...this.metrics };
  }

  /**
   * Reset metrics
   */
  resetMetrics(): void {
    this.metrics = {
      totalErrors: 0,
      retriedErrors: 0,
      circuitBreakerTrips: 0,
      averageRetryDelay: 0,
      errorsByCategory: {} as Record<ErrorCategory, number>,
      errorsBySeverity: {} as Record<ErrorSeverity, number>
    };

    Object.values(ErrorCategory).forEach(category => {
      this.metrics.errorsByCategory[category] = 0;
    });
    Object.values(ErrorSeverity).forEach(severity => {
      this.metrics.errorsBySeverity[severity] = 0;
    });
  }
}
