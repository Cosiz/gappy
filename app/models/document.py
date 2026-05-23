from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum as PyEnum

class DocumentType(str, PyEnum):
    REGULATION = "REGULATION"
    SOP = "SOP"

class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str
    doc_type: DocumentType
    version: str
    file_path: str
    uploaded_by: UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)