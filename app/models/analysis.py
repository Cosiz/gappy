from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import UUID, uuid4

class AnalysisRun(SQLModel, table=True):
    __tablename__ = "analysis_runs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    regulation_doc_id: UUID = Field(foreign_key="documents.id")
    sop_doc_ids: list[UUID] = Field(default_factory=list, sa_column=Field(sa_type=list))

    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED
    created_by: UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None