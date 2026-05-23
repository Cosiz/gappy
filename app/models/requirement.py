from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import uuid4

class Requirement(SQLModel, table=True):
    __tablename__ = "requirements"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    requirement_id: str = Field(index=True)
    document_id: str = Field(foreign_key="documents.id")
    obligation_type: str
    subject: str
    action: str
    verbatim: str
    source_section: str
    created_at: datetime = Field(default_factory=datetime.utcnow)