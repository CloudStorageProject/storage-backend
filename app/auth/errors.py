class InvalidCredentials(Exception):
    pass

class CredentialsAlreadyTaken(Exception):
    pass

class NonExistentPublicKey(Exception):
    pass

class NonExistentChallenge(Exception):
    pass

class InvalidSignature(Exception):
    pass

class InvalidToken(Exception):
    pass

class ExpiredToken(Exception):
    pass

class NonExistentUser(Exception):
    pass
