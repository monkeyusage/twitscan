class TwitscanError(Exception):
    """Exception raised for errors specific to scanning"""

    def __init__(self, message: str):
        self.message = message


class TooManyFollowersError(TwitscanError):
    def __init__(self, message: str):
        super().__init__(message)


class UserProtectedError(TwitscanError):
    def __init__(self, message: str):
        super().__init__(message)
