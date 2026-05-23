from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import UUID, uuid4

class Requirement(SQLModel, table=True):
    __tablename__ = "requirements"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    requirement_id: str = Field(index=True)  # e.g. HKMA-AI-GOV-3.2
    document_id: UUID = Field(foreign_key="documents.id")
    obligation_type: str  # SHALL / SHOULD / MAY
    subject: str
    action: str
    verbatim: str
    source_section: str
    created_at: datetime = Field(default_factory=datetime.utcnow)