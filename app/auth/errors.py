class InvalidCredentials(Exception):
    def __init__(self, message, *args):
        super().__init__(message, *args)
        self.message = message

class CredentialsAlreadyTaken(Exception):
    def __init__(self, message, *args):
        super().__init__(message, *args)
        self.message = message

class NonExistentPublicKey(Exception):
    def __init__(self, message, *args):
        super().__init__(message, *args)
        self.message = message

class NonExistentChallenge(Exception):
    def __init__(self, message, *args):
        super().__init__(message, *args)
        self.message = message

class InvalidSignature(Exception):
    def __init__(self, message, *args):
        super().__init__(message, *args)
        self.message = message