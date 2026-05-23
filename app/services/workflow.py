from app.models.finding import Finding, FindingStatus, Decision
from sqlmodel import Session
from datetime import datetime

def can_officer_review(finding: Finding) -> bool:
    return finding.status == FindingStatus.PENDING_OFFICER

def can_supervisor_review(finding: Finding) -> bool:
    return finding.status == FindingStatus.PENDING_SUPERVISOR

def submit_officer_decision(
    finding: Finding, 
    decision: Decision,
    comment: str | None,
    session: Session
) -> Finding:
    if not can_officer_review(finding):
        raise ValueError("Officer cannot review this finding at current status")

    # Record in history
    history_entry = {
        "role": "officer",
        "decision": decision.value,
        "comment": comment,
        "timestamp": datetime.utcnow().isoformat()
    }
    finding.comment_history.append(history_entry)

    finding.officer_decision = decision
    finding.officer_comment = comment

    if decision == Decision.CLARIFICATION:
        finding.status = FindingStatus.PENDING_OFFICER
    else:
        finding.status = FindingStatus.PENDING_SUPERVISOR

    session.add(finding)
    session.commit()
    session.refresh(finding)
    return finding

def submit_supervisor_decision(
    finding: Finding, 
    decision: Decision,
    comment: str | None,
    session: Session
) -> Finding:
    if not can_supervisor_review(finding):
        raise ValueError("Supervisor cannot review this finding yet")

    # Record in history
    history_entry = {
        "role": "supervisor",
        "decision": decision.value,
        "comment": comment,
        "timestamp": datetime.utcnow().isoformat()
    }
    finding.comment_history.append(history_entry)

    finding.supervisor_decision = decision
    finding.supervisor_comment = comment
    finding.status = FindingStatus.FINAL

    session.add(finding)
    session.commit()
    session.refresh(finding)
    return finding