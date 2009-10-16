class FileIntegrityError(Exception):
    def __init__(self, filename, strerror):
        self.filename = filename
        self.strerror = strerror
