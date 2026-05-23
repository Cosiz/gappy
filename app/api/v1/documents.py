from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlmodel import Session
from app.core.database import get_session
from app.services.ingestion import ingest_document
from app.models.document import DocumentType

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload")
async def upload_document(
    title: str = Form(...),
    doc_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    uploaded_by: str = Form("system"),
    session: Session = Depends(get_session)
):
    content = await file.read()
    document = ingest_document(
        title=title,
        doc_type=doc_type,
        file_content=content,
        filename=file.filename,
        uploaded_by=uploaded_by,
        session=session
    )
    return {"document_id": str(document.id), "title": document.title}