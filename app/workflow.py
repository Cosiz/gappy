"""
Workflow Engine - Phase 3

Implements the strict compliance workflow:
- PENDING_OFFICER → PENDING_SUPERVISOR → FINAL
- 30-minute undo window
- Clarification re-analysis trigger
"""

from datetime import datetime, timedelta
from typing import Optional
from app.models.finding import Finding, FindingStatus
from sqlmodel import Session

# Role definitions
class Role:
    OFFICER = "officer"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"

# Allowed transitions
ALLOWED_TRANSITIONS = {
    FindingStatus.PENDING_OFFICER: [FindingStatus.PENDING_SUPERVISOR, FindingStatus.CLARIFICATION],
    FindingStatus.PENDING_SUPERVISOR: [FindingStatus.FINAL, FindingStatus.CLARIFICATION],
    FindingStatus.CLARIFICATION: [FindingStatus.PENDING_OFFICER],
    FindingStatus.FINAL: [],
}

def can_officer_review(finding: Finding) -> bool:
    """Check if an officer can review this finding."""
    return finding.status == FindingStatus.PENDING_OFFICER

def can_supervisor_review(finding: Finding) -> bool:
    """Check if a supervisor can review this finding."""
    return finding.status == FindingStatus.PENDING_SUPERVISOR

def transition_status(
    finding: Finding,
    new_status: FindingStatus,
    actor_role: str,
    comment: Optional[str] = None,
    session: Optional[Session] = None
) -> bool:
    """
    Attempt to transition a finding to a new status.
    Returns True if successful.
    """
    current = finding.status
    
    if new_status not in ALLOWED_TRANSITIONS.get(current, []):
        return False
    
    # Role check
    if new_status == FindingStatus.PENDING_SUPERVISOR and actor_role != Role.OFFICER:
        return False
    if new_status == FindingStatus.FINAL and actor_role != Role.SUPERVISOR:
        return False
    
    finding.status = new_status
    
    # Set undo window (30 minutes) when officer makes decision
    if current == FindingStatus.PENDING_OFFICER and new_status == FindingStatus.PENDING_SUPERVISOR:
        finding.undo_until = datetime.utcnow() + timedelta(minutes=30)
    
    if comment and session:
        # Append to comment_history (simplified for now)
        if not finding.comment_history:
            finding.comment_history = []
        finding.comment_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "actor": actor_role,
            "action": f"Status changed to {new_status.value}",
            "comment": comment
        })
    
    if session:
        session.add(finding)
        session.commit()
    
    return True

def is_undo_allowed(finding: Finding) -> bool:
    """Check if undo is still allowed within the time window."""
    if not finding.undo_until:
        return False
    return datetime.utcnow() < finding.undo_until

def request_clarification(
    finding: Finding,
    actor_role: str,
    clarification_note: str,
    session: Session
) -> bool:
    """
    Request clarification on a finding.
    This should eventually trigger re-analysis (Celery task in Phase 3).
    """
    if finding.status not in [FindingStatus.PENDING_OFFICER, FindingStatus.PENDING_SUPERVISOR]:
        return False
    
    finding.status = FindingStatus.CLARIFICATION
    
    if not finding.comment_history:
        finding.comment_history = []
    
    finding.comment_history.append({
        "timestamp": datetime.utcnow().isoformat(),
        "actor": actor_role,
        "action": "Requested Clarification",
        "comment": clarification_note
    })
    
    session.add(finding)
    session.commit()
    return True
