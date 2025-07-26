import os
import docx
from pypdf import PdfReader
from .logger_config import log


def read_txt(file_path: str) -> str:
    """Reads text from a .txt file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def read_docx(file_path: str) -> str:
    """Reads text from a .docx file."""
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])


def read_pdf(file_path: str) -> str:
    """Reads text from a .pdf file."""
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def read_file(file_path: str) -> str:
    """
    Reads a file and returns its text content based on its extension.

    Args:
        file_path: The path to the file.

    Returns:
        The text content of the file.

    Raises:
        ValueError: If the file extension is not supported.
    """
    log.info(f"Reading file: {file_path}")
    _, extension = os.path.splitext(file_path)
    extension = extension.lower()

    if extension == '.txt':
        return read_txt(file_path)
    elif extension == '.docx':
        return read_docx(file_path)
    elif extension == '.pdf':
        return read_pdf(file_path)
    else:
        log.error(f"Unsupported file type attempted: {extension}")
        raise ValueError(f"Unsupported file type: {extension}")