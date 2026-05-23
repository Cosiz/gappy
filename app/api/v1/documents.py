from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, FileResponse
from typing import List
from sqlmodel import Session, select
from app.core.database import get_session
from app.services.ingestion import ingest_document
from app.models.document import Document, DocumentType
import os

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    title: str = Form(None),
    doc_type: DocumentType = Form(None),
    file: List[UploadFile] = File(None),
    uploaded_by: str = Form("system"),
    session: Session = Depends(get_session)
):

    if not doc_type:
        return RedirectResponse(
            url="/upload?error=doc_type_required",
            status_code=303
        )

    if not file or len(file) == 0:
        return RedirectResponse(
            url="/upload?error=file_required",
            status_code=303
        )

    uploaded_count = 0
    last_doc = None

    for f in file:
        if not f or not f.filename:
            continue

        # Use provided title only if single file and title is given.
        # For multiple files (or empty title), fall back to filename (without extension)
        if title and title.strip() and len(file) == 1:
            doc_title = title.strip()
        else:
            # Use filename as title (preserve original symbols, just strip extension)
            base_name = os.path.splitext(f.filename)[0]
            doc_title = base_name.strip()

        try:
            content = await f.read()
            document = ingest_document(
                title=doc_title,
                doc_type=doc_type,
                file_content=content,
                filename=f.filename,
                uploaded_by=uploaded_by,
                session=session
            )
            last_doc = document
            uploaded_count += 1
        except Exception as e:
            # Continue with other files even if one fails
            print(f"Upload failed for {f.filename}: {e}")
            continue

    if uploaded_count == 0:
        return RedirectResponse(
            url="/upload?error=upload_failed",
            status_code=303
        )

    success_msg = f"{uploaded_count} document(s) uploaded successfully"
    return RedirectResponse(
        url=f"/upload?success=1&count={uploaded_count}",
        status_code=303
    )


@router.get("/{document_id}/view")
async def view_document(
    document_id: str,
    session: Session = Depends(get_session)
):
    """Serve the uploaded PDF file for viewing/downloading."""
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(404, "Document not found")
    
    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(404, "File not found on disk")
    
    filename = os.path.basename(document.file_path)
    return FileResponse(
        path=document.file_path,
        filename=filename,
        media_type="application/pdf",
        content_disposition_type="inline"
    )


@router.post("/{document_id}/delete")
async def delete_document(
    document_id: str,
    session: Session = Depends(get_session)
):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(404, "Document not found")

    # Delete the physical file if it exists
    if document.file_path and os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
        except:
            pass  # Ignore file deletion errors

    session.delete(document)
    session.commit()

    return RedirectResponse(url="/documents?deleted=1", status_code=303)

@router.post("/{document_id}/rename")
async def rename_document(
    document_id: str,
    new_title: str = Form(...),
    session: Session = Depends(get_session)
):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(404, "Document not found")

    if new_title and new_title.strip():
        document.title = new_title.strip()
        session.add(document)
        session.commit()
        session.refresh(document)

    return RedirectResponse(url="/documents?renamed=1", status_code=303)
