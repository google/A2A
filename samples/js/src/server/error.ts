import {
  Request,
  Response,
  NextFunction
} from "express";
import * as schema from "../schema.js";

/**
 * Custom error class for A2A server operations, incorporating JSON-RPC error codes.
 */
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
    this.taskId = taskId; // Store associated task ID if provided
  }

  /**
   * Formats the error into a standard JSON-RPC error object structure.
   */
  toJSONRPCError(): schema.JSONRPCError<unknown> {
    const errorObject: schema.JSONRPCError<unknown> = {
      code: this.code,
      message: this.message,
    };
    if (this.data !== undefined) {
      errorObject.data = this.data;
    }
    return errorObject;
  }

  // Static factory methods for common errors

  static parseError(message: string, data?: unknown): A2AError {
    return new A2AError(schema.ErrorCodeParseError, message, data);
  }

  static invalidRequest(message: string, data?: unknown): A2AError {
    return new A2AError(schema.ErrorCodeInvalidRequest, message, data);
  }

  static methodNotFound(method: string): A2AError {
    return new A2AError(
      schema.ErrorCodeMethodNotFound,
      `Method not found: ${method}`
    );
  }

  static invalidParams(message: string, data?: unknown): A2AError {
    return new A2AError(schema.ErrorCodeInvalidParams, message, data);
  }

  static internalError(message: string, data?: unknown): A2AError {
    return new A2AError(schema.ErrorCodeInternalError, message, data);
  }

  static taskNotFound(taskId: string): A2AError {
    return new A2AError(
      schema.ErrorCodeTaskNotFound,
      `Task not found: ${taskId}`,
      undefined,
      taskId
    );
  }

  static taskNotCancelable(taskId: string): A2AError {
    return new A2AError(
      schema.ErrorCodeTaskNotCancelable,
      `Task not cancelable: ${taskId}`,
      undefined,
      taskId
    );
  }

  static pushNotificationNotSupported(): A2AError {
    return new A2AError(
      schema.ErrorCodePushNotificationNotSupported,
      "Push Notification is not supported"
    );
  }

  static unsupportedOperation(operation: string): A2AError {
    return new A2AError(
      schema.ErrorCodeUnsupportedOperation,
      `Unsupported operation: ${operation}`
    );
  }
}

/** Express error handling middleware */
export function errorHandler(
  err: any,
  req: Request,
  res: Response,
  next: NextFunction // eslint-disable-line @typescript-eslint/no-unused-vars
) {
  // If headers already sent (likely streaming), just log and end.
  // The stream handler should have sent an error event if possible.
  if (res.headersSent) {
    console.error(
      `[ErrorHandler] Error after headers sent (ReqID: ${
        req.body?.id ?? "N/A"
      }, TaskID: ${err?.taskId ?? "N/A"}):`,
      err
    );
    // Ensure the response is ended if it wasn't already
    if (!res.writableEnded) {
      res.end();
    }
    return;
  }

  let responseError: schema.JSONRPCResponse<null, unknown>;

  if (err instanceof A2AError) {
    // Already normalized somewhat by the endpoint handler
    responseError = normalizeError(
      err,
      req.body?.id ?? null,
      err.taskId
    );
  } else {
    // Normalize other errors caught by Express itself (e.g., JSON parse errors)
    let reqId = null;
    try {
      // Try to parse body again to get ID, might fail
      const body = JSON.parse(req.body); // Assumes body might be raw string on parse fail
      reqId = body?.id ?? null;
    } catch (_) {
      /* Ignore parsing errors */
    }

    // Check for Express/body-parser JSON parsing error
    if (
      err instanceof SyntaxError &&
      "body" in err &&
      "status" in err &&
      err.status === 400
    ) {
      responseError = normalizeError(
        A2AError.parseError(err.message),
        reqId
      );
    } else {
      responseError = normalizeError(err, reqId); // Normalize other unexpected errors
    }
  }

  res.status(200); // JSON-RPC errors use 200 OK, error info is in the body
  res.json(responseError);
};

function createErrorResponse(
  id: number | string | null | undefined,
  error: schema.JSONRPCError<unknown>
): schema.JSONRPCResponse<null, unknown> {
  // For errors, ID should be the same as request ID, or null if that couldn't be determined
  return {
    jsonrpc: "2.0",
    id: id, // Can be null if request ID was invalid/missing
    error: error,
  };
}

/** Normalizes various error types into a JSONRPCResponse containing an error */
export function normalizeError(
  error: any,
  reqId: number | string | null | undefined,
  taskId?: string
): schema.JSONRPCResponse<null, unknown> {
  let a2aError: A2AError;
  if (error instanceof A2AError) {
    a2aError = error;
  } else if (error instanceof Error) {
    // Generic JS error
    a2aError = A2AError.internalError(error.message, { stack: error.stack });
  } else {
    // Unknown error type
    a2aError = A2AError.internalError("An unknown error occurred.", error);
  }

  // Ensure Task ID context is present if possible
  if (taskId && !a2aError.taskId) {
    a2aError.taskId = taskId;
  }

  console.error(
    `Error processing request (Task: ${a2aError.taskId ?? "N/A"}, ReqID: ${
      reqId ?? "N/A"
    }):`,
    a2aError
  );

  return createErrorResponse(reqId, a2aError.toJSONRPCError());
}

