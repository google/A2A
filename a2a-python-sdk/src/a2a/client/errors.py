class A2AClientError(Exception):
    """Base exception for client A2A Client errors."""


class A2AClientHTTPError(A2AClientError):
    """Client exception for HTTP errors."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f'HTTP Error {status_code}: {message}')


class A2AClientJSONError(A2AClientError):
    """Client exception for JSON errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(f'JSON Error: {message}')
