from werkzeug.datastructures import FileStorage
################################################################################

def save_filestorage_to_temp_docx(uploaded_file: FileStorage) -> str:
    import tempfile
    tmpdir = tempfile.mkdtemp(prefix="docxparse_")
    import os
    docx_path = os.path.join(tmpdir, "tempfile.docx")
    import shutil
    uploaded_file.stream.seek(0)
    with open(docx_path, 'wb') as f:
        shutil.copyfileobj(uploaded_file.stream, f)
    return docx_path
