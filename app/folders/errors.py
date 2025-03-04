class FolderNotFound(Exception):
    def __init__(self, message, *args):
        super().__init__(message, *args)
        self.message = message


class FolderNameAlreadyTakenInParent(Exception):
    def __init__(self, message, *args):
        super().__init__(message, *args)
        self.message = message


class CannotModifyRootFolder(Exception):
    def __init__(self, message, *args):
        super().__init__(message, *args)
        self.message = message