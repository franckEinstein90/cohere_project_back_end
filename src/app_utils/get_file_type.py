from enum import Enum
from werkzeug.datastructures import FileStorage
################################################################################


class FileType(str, Enum):
    TEXT = "text"
    PDF = "pdf"
    DOCX = "docx"
    UNKNOWN = "unknown"
################################################################################
def get_file_type(uploaded_file: FileStorage) -> str:
    if uploaded_file.filename.lower().endswith('.pdf'):
        return FileType.PDF.value
    elif uploaded_file.filename.lower().endswith('.docx'):
        return FileType.DOCX.value

    return FileType.UNKNOWN.value