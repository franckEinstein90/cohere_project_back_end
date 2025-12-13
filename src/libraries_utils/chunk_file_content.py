from typing import List
from werkzeug.datastructures import FileStorage
from .errors import FileProcessingError
from .chunk_docx_content import chunk_docx_content

from src.app_utils import get_file_type, FileType
from src.schemas import ChunkConfig

def chunk_file_content(
    uploaded_file: FileStorage,
    chunk_config: ChunkConfig
) -> List[str]:
    """Dispatch chunking based on file type.

    Uses `get_file_type` to detect file type and calls the appropriate
    chunker. Raises FileProcessingError for unsupported types or failures.
    """
    try:
        filetype = get_file_type(uploaded_file)
        if filetype == FileType.PDF.value:
            # Import here to avoid heavy deps at module import time
            from .chunk_pdf_content import chunk_pdf_content
            return chunk_pdf_content(uploaded_file, chunk_config)

        if filetype == FileType.DOCX.value:
            from .chunk_docx_content import chunk_docx_content
            return chunk_docx_content(uploaded_file, chunk_config)
        raise FileProcessingError(
                f"Unsupported file type for chunking: {filetype}"
            )

    except FileProcessingError:
        raise
    except Exception as e:
        raise FileProcessingError(f"Failed to read uploaded file: {str(e)}")
    