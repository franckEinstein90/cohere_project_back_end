class FileProcessingError(Exception):
    """Base exception for file processing errors."""
    pass


class InvalidFileError(FileProcessingError):
    """Raised when file validation fails."""
    pass


class StorageError(FileProcessingError):
    """Raised when file storage operations fail."""
    pass


class MetadataError(FileProcessingError):
    """Raised when metadata processing fails."""
    pass

