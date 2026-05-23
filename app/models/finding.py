from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON
from datetime import datetime
from uuid import uuid4
from enum import Enum as PyEnum

class FindingLabel(str, PyEnum):
    COVERED = "COVERED"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"

class Decision(str, PyEnum):
    ACCEPT = "ACCEPT"
    DISPUTE = "DISPUTE"
    CLARIFICATION = "CLARIFICATION"

class FindingStatus(str, PyEnum):
    PENDING_OFFICER = "PENDING_OFFICER"
    PENDING_SUPERVISOR = "PENDING_SUPERVISOR"
    FINAL = "FINAL"

class Finding(SQLModel, table=True):
    __tablename__ = "findings"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    analysis_id: str = Field(foreign_key="analysis_runs.id")
    requirement_id: str

    label: FindingLabel
    confidence: float
    rationale: str

    supporting_anchors: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    missing_aspects: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    officer_decision: Decision | None = None
    officer_comment: str | None = None
    supervisor_decision: Decision | None = None
    supervisor_comment: str | None = None

    # New: Comment history for audit trail
    comment_history: list[dict] = Field(default_factory=list, sa_column=Column(JSON))

    status: FindingStatus = FindingStatus.PENDING_OFFICER

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)