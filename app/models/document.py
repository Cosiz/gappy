from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import uuid4
from enum import Enum as PyEnum

class DocumentType(str, PyEnum):
    REGULATION = "REGULATION"
    SOP = "SOP"

class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    title: str
    doc_type: DocumentType
    version: str
    file_path: str
    uploaded_by: str | None = Field(default="system")
    created_at: datetime = Field(default_factory=datetime.utcnow)