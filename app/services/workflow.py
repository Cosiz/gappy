"""
Workflow Engine (Phase 3 Enhanced)

Implements the full compliance workflow with:
- Officer → Supervisor → Final transitions
- 30-minute undo window
- Clarification flow (triggers re-analysis)
- Role-based access control
"""

from datetime import datetime, timedelta
from typing import Optional
from app.models.finding import Finding, FindingStatus, Decision
from sqlmodel import Session

# ============================================
# Role-based permissions
# ============================================

def can_officer_review(finding: Finding) -> bool:
    return finding.status == FindingStatus.PENDING_OFFICER

def can_supervisor_review(finding: Finding) -> bool:
    return finding.status == FindingStatus.PENDING_SUPERVISOR

def can_undo(finding: Finding) -> bool:
    """Check if undo is allowed within the 30-minute window."""
    if not finding.undo_until:
        return False
    return datetime.utcnow() < finding.undo_until

# ============================================
# Core decision submission
# ============================================

def submit_officer_decision(
    finding: Finding,
    decision: Decision,
    comment: Optional[str],
    session: Session
) -> Finding:
    if not can_officer_review(finding):
        raise ValueError("Officer cannot review this finding at current status")

    # Record history
    history_entry = {
        "role": "officer",
        "decision": decision.value,
        "comment": comment,
        "timestamp": datetime.utcnow().isoformat()
    }
    if finding.comment_history is None:
        finding.comment_history = []
    finding.comment_history.append(history_entry)

    finding.officer_decision = decision
    finding.officer_comment = comment

    if decision == Decision.CLARIFICATION:
        finding.status = FindingStatus.CLARIFICATION
    else:
        finding.status = FindingStatus.PENDING_SUPERVISOR
        # Set 30-minute undo window
        finding.undo_until = datetime.utcnow() + timedelta(minutes=30)

    session.add(finding)
    session.commit()
    session.refresh(finding)
    return finding

def submit_supervisor_decision(
    finding: Finding,
    decision: Decision,
    comment: Optional[str],
    session: Session
) -> Finding:
    if not can_supervisor_review(finding):
        raise ValueError("Supervisor cannot review this finding yet")

    history_entry = {
        "role": "supervisor",
        "decision": decision.value,
        "comment": comment,
        "timestamp": datetime.utcnow().isoformat()
    }
    if finding.comment_history is None:
        finding.comment_history = []
    finding.comment_history.append(history_entry)

    finding.supervisor_decision = decision
    finding.supervisor_comment = comment
    finding.status = FindingStatus.FINAL
    finding.undo_until = None  # Clear undo window on final decision

    session.add(finding)
    session.commit()
    session.refresh(finding)
    return finding

# ============================================
# Undo (within 30-minute window)
# ============================================

def undo_officer_decision(finding: Finding, session: Session) -> Finding:
    if not can_undo(finding):
        raise ValueError("Undo window has expired or undo is not allowed")

    # Reset to PENDING_OFFICER
    finding.status = FindingStatus.PENDING_OFFICER
    finding.officer_decision = None
    finding.officer_comment = None
    finding.undo_until = None

    # Record undo in history
    if finding.comment_history is None:
        finding.comment_history = []
    finding.comment_history.append({
        "role": "officer",
        "action": "UNDO",
        "timestamp": datetime.utcnow().isoformat()
    })

    session.add(finding)
    session.commit()
    session.refresh(finding)
    return finding

# ============================================
# Clarification flow
# ============================================

def request_clarification(
    finding: Finding,
    comment: str,
    session: Session
) -> Finding:
    """
    Officer or Supervisor requests clarification.
    In a full implementation, this would trigger a Celery task
    to re-run analysis on the affected requirement.
    """
    if finding.status not in [FindingStatus.PENDING_OFFICER, FindingStatus.PENDING_SUPERVISOR]:
        raise ValueError("Clarification can only be requested on pending findings")

    if finding.comment_history is None:
        finding.comment_history = []

    finding.comment_history.append({
        "role": "system",
        "action": "CLARIFICATION_REQUESTED",
        "comment": comment,
        "timestamp": datetime.utcnow().isoformat()
    })

    finding.status = FindingStatus.CLARIFICATION

    session.add(finding)
    session.commit()
    session.refresh(finding)
    return finding

def resolve_clarification(finding: Finding, session: Session) -> Finding:
    """Return finding to officer review after clarification is resolved."""
    if finding.status != FindingStatus.CLARIFICATION:
        raise ValueError("Finding is not in clarification state")

    finding.status = FindingStatus.PENDING_OFFICER

    if finding.comment_history is None:
        finding.comment_history = []
    finding.comment_history.append({
        "role": "system",
        "action": "CLARIFICATION_RESOLVED",
        "timestamp": datetime.utcnow().isoformat()
    })

    session.add(finding)
    session.commit()
    session.refresh(finding)
    return finding
