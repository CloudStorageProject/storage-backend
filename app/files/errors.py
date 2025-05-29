class FileAlreadyExistsInThisFolder(Exception):
    pass

class FileUploadError(Exception):
    pass

class FileRetrieveError(Exception):
    pass

class FileDoesNotExist(Exception):
    pass

class FileDeletionError(Exception):
    pass

class SpaceLimitExceeded(Exception):
    pass

class DestinationUserDoesNotExist(Exception):
    pass

class FileAlreadyShared(Exception):
    pass

class CannotShareWithYourself(Exception):
    pass

class FileIsNotShared(Exception):
    pass
