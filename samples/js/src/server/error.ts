import * as schema from "../schema.js";

/** Custom error class for A2A server operations. */
export class A2AError extends Error {
  public code: schema.KnownErrorCode | number;
  public data?: unknown;
  public taskId?: string; // Optional task ID context

  constructor(
    code: schema.KnownErrorCode | number,
    message: string,
    data?: unknown,
    taskId?: string
  ) {
    super(message);
    this.name = "A2AError";
    this.code = code;
    this.data = data;
    this.taskId = taskId;
  }

  /** Formats the error into a standard JSON-RPC error object. */
  toJSONRPCError(): schema.JSONRPCError<unknown> {
    const errorObject: schema.JSONRPCError<unknown> = {
      code: this.code,
      message: this.message,
    };
    // Only include data if it's defined (handles both null and other values)
    if (this.data !== undefined) {
      errorObject.data = this.data;
    }
    return errorObject;
  }

  // --- Static factory methods ---

  static parseError(message: string, data?: unknown): A2AError {
    return new A2AError(schema.ErrorCodeParseError, message, data);
  }
  static invalidRequest(message: string, data?: unknown): A2AError {
    return new A2AError(schema.ErrorCodeInvalidRequest, message, data);
  }
  static methodNotFound(method: string): A2AError {
    // data MUST be null for this error according to schema fix
    return new A2AError(schema.ErrorCodeMethodNotFound, `Method not found: ${method}`, null);
  }
  static invalidParams(message: string, data?: unknown): A2AError {
    return new A2AError(schema.ErrorCodeInvalidParams, message, data);
  }
  static internalError(message: string, data?: unknown): A2AError {
    return new A2AError(schema.ErrorCodeInternalError, message, data);
  }
  static taskNotFound(taskId: string): A2AError {
     // data MUST be null
    return new A2AError(schema.ErrorCodeTaskNotFound, `Task not found: ${taskId}`, null, taskId);
  }
  static taskNotCancelable(taskId: string): A2AError {
     // data MUST be null
    return new A2AError(schema.ErrorCodeTaskNotCancelable, `Task not cancelable: ${taskId}`, null, taskId);
  }
  static pushNotificationNotSupported(): A2AError {
     // data MUST be null
    return new A2AError(schema.ErrorCodePushNotificationNotSupported, "Push Notification is not supported", null);
  }
  static unsupportedOperation(operation: string): A2AError {
     // data MUST be null
    return new A2AError(schema.ErrorCodeUnsupportedOperation, `Unsupported operation: ${operation}`, null);
  }
   static contentTypeNotSupported(): A2AError {
     // data MUST be null
    return new A2AError(schema.ErrorCodeContentTypeNotSupported, "Incompatible content types", null);
  }

   // --- NEW KG/Alignment Error Factories ---
   static knowledgeQueryError(message: string, data?: unknown): A2AError {
    return new A2AError(schema.ErrorCodeKnowledgeQueryError, message, data);
  }
   static knowledgeUpdateError(message: string, data?: unknown): A2AError {
    return new A2AError(schema.ErrorCodeKnowledgeUpdateError, message, data);
  }
   static knowledgeSubscriptionError(message: string, data?: unknown): A2AError {
    return new A2AError(schema.ErrorCodeKnowledgeSubscriptionError, message, data);
  }
   static alignmentViolationError(message: string, data?: unknown): A2AError {
    return new A2AError(schema.ErrorCodeAlignmentViolationError, message, data);
  }
}
