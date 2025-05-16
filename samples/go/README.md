# A2A Go Implementation

> **Note**: This is sample code for demonstration purposes only. It is not intended for production use. The implementation is simplified and lacks important production features such as proper error handling, security measures, and performance optimizations.

This directory contains a Go implementation of the Agent-to-Agent (A2A) communication protocol.

## Overview

The implementation follows the JSON-RPC 2.0 specification and provides:

- JSON-RPC 2.0 compliant server and client
- Task management (send, get, cancel)
- Error handling with A2A error codes
- Thread-safe task storage
- Comprehensive test coverage

## Project Structure

```
go/
├── server/         # Server implementation
├── client/         # Client implementation
└── models/         # Shared data structures
```

## Getting Started

1. Install Go 1.21 or later
2. Clone the repository
3. Run the tests:
   ```bash
   cd samples/go
   go test ./...
   ```

## Documentation

- [Server Documentation](server/README.md)
- [Client Documentation](client/README.md)
- [Models Documentation](models/README.md)

## Testing

Run the test suite:

```bash
go test ./...
```

## License

MIT License 