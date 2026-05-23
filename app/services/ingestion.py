import fitz  # PyMuPDF
from pathlib import Path
from uuid import uuid4
from app.models.document import Document, DocumentType
from sqlmodel import Session

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF using PyMuPDF. Returns empty string on failure."""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception:
        return "[PDF text extraction failed]"

def save_uploaded_file(file_content: bytes, filename: str) -> str:
    """Save uploaded file and return path"""
    file_id = uuid4().hex[:8]
    safe_name = f"{file_id}_{filename}"
    file_path = UPLOAD_DIR / safe_name

    with open(file_path, "wb") as f:
        f.write(file_content)

    return str(file_path)

def ingest_document(
    title: str,
    doc_type: DocumentType,
    file_content: bytes,
    filename: str,
    uploaded_by: str,
    session: Session
) -> Document:
    """Ingest a document: save file + extract text + store in DB"""

    file_path = save_uploaded_file(file_content, filename)
    text = extract_text_from_pdf(file_path)

    document = Document(
        title=title,
        doc_type=doc_type,
        version="1.0",
        file_path=file_path,
        uploaded_by=uploaded_by
    )

    session.add(document)
    session.commit()
    session.refresh(document)

    return document