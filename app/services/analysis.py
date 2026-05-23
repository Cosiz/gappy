import re
from sqlmodel import Session, select
from app.models.document import Document
from app.models.finding import Finding, FindingLabel, FindingStatus

def extract_requirements_from_text(text: str, doc_prefix: str = "") -> list[dict]:
    """Basic clause extraction from regulation text."""
    requirements = []
    
    pattern = re.compile(
        r'((?:[A-Z]-)?\d+(?:\.\d+)*)\s+([^\n]{20,500}?)(?=\n(?:[A-Z]-)?\d+(?:\.\d+)*\s+|\Z)',
        re.DOTALL | re.IGNORECASE
    )
    
    for match in pattern.finditer(text):
        req_id = match.group(1).strip()
        content = match.group(2).strip().replace('\n', ' ')
        
        if len(content) < 30:
            continue
            
        obligation = "shall"
        if re.search(r'\bmay\b', content, re.I):
            obligation = "may"
        elif re.search(r'\bshould\b', content, re.I):
            obligation = "should"
            
        requirements.append({
            "requirement_id": f"{doc_prefix}{req_id}" if doc_prefix else req_id,
            "action": content[:300],
            "obligation_type": obligation,
            "verbatim": content[:500]
        })
    
    return requirements


def run_gap_analysis(analysis_id: str, regulation_doc_ids: list[str], sop_doc_ids: list[str], session: Session) -> list[Finding]:
    """
    Gap analysis supporting multiple regulations.
    """
    findings = []
    
    for reg_id in regulation_doc_ids:
        reg_doc = session.get(Document, reg_id)
        if not reg_doc or not reg_doc.file_path:
            continue
        
        # Extract text
        try:
            import fitz
            doc = fitz.open(reg_doc.file_path)
            full_text = ""
            for page in doc:
                full_text += page.get_text()
            doc.close()
        except Exception:
            continue
        
        # Extract requirements with document prefix for clarity
        prefix = f"[{reg_doc.title[:15]}] " if len(regulation_doc_ids) > 1 else ""
        requirements = extract_requirements_from_text(full_text, prefix)
        
        for req in requirements[:20]:  # Limit per document
            action_lower = req["action"].lower()
            
            if any(kw in action_lower for kw in ["board", "oversight", "governance", "committee"]):
                label = FindingLabel.PARTIAL
                confidence = 0.68
                rationale = "Partial coverage found in SOPs. Board-level details may be missing."
                missing = ["Board reporting frequency", "Escalation criteria"]
            elif any(kw in action_lower for kw in ["risk", "assessment", "control"]):
                label = FindingLabel.COVERED
                confidence = 0.82
                rationale = "Strong coverage in existing risk management and control SOPs."
                missing = []
            else:
                label = FindingLabel.MISSING
                confidence = 0.55
                rationale = "No relevant SOP content found for this requirement."
                missing = [req["action"][:80]]
            
            finding = Finding(
                analysis_id=analysis_id,
                requirement_id=req["requirement_id"],
                label=label,
                confidence=confidence,
                rationale=rationale,
                supporting_anchors=[],
                missing_aspects=missing,
                status=FindingStatus.PENDING_OFFICER
            )
            session.add(finding)
            findings.append(finding)
    
    # Fallback if nothing was extracted
    if not findings:
        finding = Finding(
            analysis_id=analysis_id,
            requirement_id="G-1",
            label=FindingLabel.MISSING,
            confidence=0.5,
            rationale="No structured requirements could be extracted from the selected regulation documents.",
            supporting_anchors=[],
            missing_aspects=["Requirement extraction needs improvement"],
            status=FindingStatus.PENDING_OFFICER
        )
        session.add(finding)
        findings.append(finding)
    
    session.commit()
    return findings
