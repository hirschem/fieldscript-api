class PayloadTooLargeError(Exception):
    error_code = "PAYLOAD_TOO_LARGE"
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
