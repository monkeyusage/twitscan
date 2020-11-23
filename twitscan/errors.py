class TwitscanError(Exception):
    """Exception raised for errors specific to scanning"""

    def __init__(self, message: str):
        self.message = message
