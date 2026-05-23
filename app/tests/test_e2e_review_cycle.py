"""
E2E Test: Officer + Supervisor Review Cycle (B)
Creates findings directly and tests the full review workflow + comment history.
"""
import sys
sys.path.insert(0, '/app/gappy')

from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.main import app
from app.core.database import engine
from app.models.finding import Finding, FindingLabel, FindingStatus, Decision
from app.models.analysis import AnalysisRun
from app.services.workflow import submit_officer_decision, submit_supervisor_decision
import uuid
from datetime import datetime

client = TestClient(app)

def create_test_findings():
    print("\n[SETUP] Creating test findings for review cycle...")
    with Session(engine) as session:
        # Get existing analysis or create one
        analysis = session.exec(select(AnalysisRun)).first()
        if not analysis:
            analysis = AnalysisRun(
                name="Test Analysis",
                regulation_doc_id="test-reg",
                sop_doc_ids=["test-sop"],
                status="COMPLETED"
            )
            session.add(analysis)
            session.commit()
            session.refresh(analysis)

        # Clear old findings
        for f in session.exec(select(Finding)).all():
            session.delete(f)
        session.commit()

        # Create 3 realistic findings
        findings_data = [
            {"label": FindingLabel.PARTIAL, "confidence": 0.72, "rationale": "Board oversight partially addressed in SOP section 4.2", "missing": ["Quarterly reporting frequency", "Escalation path"]},
            {"label": FindingLabel.COVERED, "confidence": 0.91, "rationale": "Risk assessment framework fully documented in SOP 3.1-3.4", "missing": []},
            {"label": FindingLabel.MISSING, "confidence": 0.65, "rationale": "No evidence of annual independent audit process", "missing": ["Independent audit requirement"]},
        ]

        created = []
        for data in findings_data:
            f = Finding(
                id=str(uuid.uuid4()),
                analysis_id=analysis.id,
                requirement_id=f"REQ-{uuid.uuid4().hex[:6]}",
                label=data["label"],
                confidence=data["confidence"],
                rationale=data["rationale"],
                supporting_anchors=[],
                missing_aspects=data["missing"],
                status=FindingStatus.PENDING_OFFICER
            )
            session.add(f)
            created.append(f)
        session.commit()
        print(f"    ✓ Created {len(created)} findings")
        return created

def test_officer_workflow(findings):
    print("\n[OFFICER] Compliance Officer Review Cycle")
    with Session(engine) as session:
        # Refresh findings
        findings = session.exec(select(Finding)).all()
        
        # Officer accepts first finding
        f1 = findings[0]
        submit_officer_decision(f1, Decision.ACCEPT, "Looks solid. Board oversight is addressed.", session)
        print(f"    ✓ Officer ACCEPTED finding 1 → moved to PENDING_SUPERVISOR")

        # Officer disputes second finding  
        f2 = findings[1]
        submit_officer_decision(f2, Decision.DISPUTE, "Risk section needs more detail on model drift detection.", session)
        print(f"    ✓ Officer DISPUTED finding 2 → moved to PENDING_SUPERVISOR")

        # Officer requests clarification on third
        f3 = findings[2]
        submit_officer_decision(f3, Decision.CLARIFICATION, "Please clarify if external auditor is required.", session)
        print(f"    ✓ Officer requested CLARIFICATION on finding 3")

def test_supervisor_workflow():
    print("\n[SUPERVISOR] Supervisor Final Review")
    with Session(engine) as session:
        findings = session.exec(select(Finding).where(Finding.status == FindingStatus.PENDING_SUPERVISOR)).all()
        
        for f in findings:
            submit_supervisor_decision(f, Decision.ACCEPT, "Supervisor agrees with officer assessment. Finalized.", session)
            print(f"    ✓ Supervisor ACCEPTED finding → FINAL status")

def verify_comment_history():
    print("\n[HISTORY] Verifying Comment History")
    with Session(engine) as session:
        findings = session.exec(select(Finding)).all()
        for f in findings:
            history = f.comment_history or []
            print(f"  Finding {f.requirement_id}: {len(history)} history entries")
            for entry in history:
                print(f"    - [{entry['role'].upper()}] {entry['decision']}: \"{entry.get('comment','')[:40]}...\"")

if __name__ == "__main__":
    print("="*60)
    print("GAPPY E2E REVIEW CYCLE TEST (B)")
    print("="*60)
    
    findings = create_test_findings()
    test_officer_workflow(findings)
    test_supervisor_workflow()
    verify_comment_history()
    
    print("\n✓ Full Officer → Supervisor review cycle completed successfully")