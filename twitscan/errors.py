class TwitscanError(Exception):
    """Exception raised for errors specific to scanning"""
    def __init__(self, expression:str, message:str):
        self.expression = expression
        self.message = message