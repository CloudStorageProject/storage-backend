class FileAlreadyExistsInThisFolder(Exception):
    def __init__(self, message, *args):
        super().__init__(message, *args)
        self.message = message

class FileUploadError(Exception):
    def __init__(self, message, *args):
        super().__init__(message, *args)
        self.message = message

class BucketCreationError(Exception):
    def __init__(self, message, *args):
        super().__init__(message, *args)
        self.message = message

class FileRetrieveError(Exception):
    def __init__(self, message, *args):
        super().__init__(message, *args)
        self.message = message

class FileDoesNotExist(Exception):
    def __init__(self, message, *args):
        super().__init__(message, *args)
        self.message = message

class FileDeletionError(Exception):
    def __init__(self, message, *args):
        super().__init__(message, *args)
        self.message = message