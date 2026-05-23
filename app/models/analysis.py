from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON
from datetime import datetime
from uuid import uuid4

class AnalysisRun(SQLModel, table=True):
    __tablename__ = "analysis_runs"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str
    regulation_doc_id: str | None = Field(default=None, foreign_key="documents.id")  # legacy single value
    regulation_doc_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    sop_doc_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    status: str = "PENDING"
    created_by: str | None = Field(default="system")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None