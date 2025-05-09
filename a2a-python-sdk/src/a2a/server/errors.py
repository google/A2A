class A2AServerError(Exception):
    """Base exception for  A2A Server errors."""


class MethodNotImplementedError(A2AServerError):
    """Exception for Unimplemented methods."""

    def __init__(
        self, message: str = 'This method is not implemented by the server'
    ):
        self.message = message
        super().__init__(f'Not Implemented operation Error: {message}')
