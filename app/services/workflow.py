from app.models.finding import Finding, FindingStatus, Decision
from sqlmodel import Session

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

    finding.officer_decision = decision
    finding.officer_comment = comment

    if decision == Decision.CLARIFICATION:
        finding.status = FindingStatus.PENDING_OFFICER  # Will be re-analyzed
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

    finding.supervisor_decision = decision
    finding.supervisor_comment = comment
    finding.status = FindingStatus.FINAL

    session.add(finding)
    session.commit()
    session.refresh(finding)
    return finding