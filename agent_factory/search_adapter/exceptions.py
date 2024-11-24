class UsageLimitExceededError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class BadRequestError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class InvalidTavilyAPIKeyError(Exception):
    def __init__(self):
        super().__init__("Tavily API key invalid.")
