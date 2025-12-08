from typing import Tuple
################################################################################
from .errors import InvalidFileError
################################################################################

def read_uploaded_file(uploaded_file) -> tuple[str, str]:
    """Read and decode uploaded file content.
    
    Args:
        uploaded_file: Flask file object from request.files
        
    Returns:
        Tuple of (filename, content)
        
    Raises:
        InvalidFileError: If file cannot be read or decoded
    """
    if not uploaded_file or not uploaded_file.filename:
        raise InvalidFileError("No file selected")
    
    filename = uploaded_file.filename
    
    try:
        content = uploaded_file.read().decode('utf-8')
    except UnicodeDecodeError as e:
        raise InvalidFileError(f"File must be UTF-8 encoded text: {str(e)}")
    except Exception as e:
        raise InvalidFileError(f"Failed to read file: {str(e)}")
    
    return filename, content