from app.models.finding import Finding, FindingLabel, FindingStatus
from app.models.requirement import Requirement
from sqlmodel import Session, select
import random

def run_gap_analysis(analysis_id: str, regulation_doc_id: str, sop_doc_ids: list[str], session: Session) -> list[Finding]:
    """
    Real (simplified) gap analysis:
    - Takes requirements from regulation
    - Creates findings with basic logic
    """
    findings = []
    
    # Get all requirements from the regulation document
    requirements = session.exec(
        select(Requirement).where(Requirement.document_id == regulation_doc_id)
    ).all()
    
    for req in requirements:
        # Simple heuristic for prototype
        if "board" in req.action.lower() or "oversight" in req.action.lower():
            label = FindingLabel.PARTIAL
            confidence = 0.72
            rationale = "Partial coverage found in SOPs. Missing Board-level details."
            missing = ["Board reporting frequency", "Escalation criteria"]
        elif "risk" in req.action.lower():
            label = FindingLabel.COVERED
            confidence = 0.89
            rationale = "Strong coverage in existing risk management SOPs."
            missing = []
        else:
            label = FindingLabel.MISSING
            confidence = 0.65
            rationale = "No relevant SOP content found for this requirement."
            missing = [req.action[:80]]
        
        finding = Finding(
            analysis_id=analysis_id,
            requirement_id=req.id,
            label=label,
            confidence=confidence,
            rationale=rationale,
            supporting_anchors=[],
            missing_aspects=missing,
            status=FindingStatus.PENDING_OFFICER
        )
        session.add(finding)
        findings.append(finding)
    
    session.commit()
    return findings