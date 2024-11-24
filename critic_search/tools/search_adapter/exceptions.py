class SearchClientError(Exception):
    def __init__(self, message: str = "An error occurred in the search client."):
        super().__init__(message)


class UsageLimitExceededError(SearchClientError):
    def __init__(self, message: str = "Usage limit exceeded."):
        super().__init__(message)


class BadRequestError(SearchClientError):
    def __init__(self, message: str = "Bad request."):
        super().__init__(message)


class InvalidAPIKeyError(SearchClientError):
    def __init__(self, message: str = "Invalid API key."):
        super().__init__(message)


class RatelimitException(SearchClientError):
    def __init__(self, message: str = "Rate limit exceeded."):
        super().__init__(message)


class TimeoutException(SearchClientError):
    def __init__(self, message: str = "Timeout occurred."):
        super().__init__(message)
