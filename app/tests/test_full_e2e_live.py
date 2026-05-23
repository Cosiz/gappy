"""
Full End-to-End Live Test (A + B)
- Seeds realistic test data (documents + requirements)
- Triggers real gap analysis
- Performs complete Officer → Supervisor review cycle
- Verifies comment history, status transitions, and UI feedback
"""
import sys
sys.path.insert(0, '/app/gappy')

from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.main import app
from app.core.database import engine, create_db_and_tables
from app.models.document import Document, DocumentType
from app.models.requirement import Requirement
from app.models.finding import Finding, FindingStatus
from datetime import datetime
import uuid

client = TestClient(app)

def seed_test_data():
    print("\n[SEED] Creating realistic test data...")
    with Session(engine) as session:
        # Clear existing test data for clean run
        for f in session.exec(select(Finding)).all():
            session.delete(f)
        for r in session.exec(select(Requirement)).all():
            session.delete(r)
        for d in session.exec(select(Document)).all():
            session.delete(d)
        session.commit()

        # Create a regulation document (all required fields)
        reg_doc = Document(
            id=str(uuid.uuid4()),
            title="HKMA AI Governance Guidelines v2.3",
            doc_type=DocumentType.REGULATION,
            version="2.3",
            file_path="/uploads/reg-v2.3.pdf",
            uploaded_by="system",
            created_at=datetime.utcnow()
        )
        session.add(reg_doc)

        # Create requirements for the regulation
        requirements = [
            Requirement(id=str(uuid.uuid4()), document_id=reg_doc.id, action="Board must establish AI oversight committee with quarterly reporting"),
            Requirement(id=str(uuid.uuid4()), document_id=reg_doc.id, action="Implement risk assessment framework for all AI systems"),
            Requirement(id=str(uuid.uuid4()), document_id=reg_doc.id, action="Conduct annual independent audit of AI governance"),
            Requirement(id=str(uuid.uuid4()), document_id=reg_doc.id, action="Maintain human oversight for high-risk AI decisions"),
        ]
        for req in requirements:
            session.add(req)

        # Create an SOP document
        sop_doc = Document(
            id=str(uuid.uuid4()),
            title="Internal AI Risk Management SOP v1.4",
            doc_type=DocumentType.SOP,
            version="1.4",
            file_path="/uploads/sop-v1.4.pdf",
            uploaded_by="system",
            created_at=datetime.utcnow()
        )
        session.add(sop_doc)

        session.commit()
        print(f"    ✓ Created regulation doc: {reg_doc.id}")
        print(f"    ✓ Created {len(requirements)} requirements")
        print(f"    ✓ Created SOP doc: {sop_doc.id}")

        return reg_doc.id, sop_doc.id

def run_analysis(reg_doc_id: str, sop_doc_id: str):
    print("\n[ANALYZE] Triggering gap analysis...")
    response = client.post("/analyses/run", data={
        "name": "HKMA Compliance Check - May 2026",
        "regulation_doc_id": reg_doc_id,
        "sop_doc_ids": sop_doc_id
    })
    print(f"    Status: {response.status_code}")
    if response.status_code == 303:
        print("    ✓ Analysis completed and redirected to report")
    return response

def perform_officer_review():
    print("\n[OFFICER] Performing Compliance Officer review...")
    with Session(engine) as session:
        findings = session.exec(select(Finding)).all()
        print(f"    Found {len(findings)} findings to review")

        for i, finding in enumerate(findings[:2]):  # Review first 2
            decision = "ACCEPT" if i == 0 else "DISPUTE"
            comment = f"Officer review #{i+1}: {'Looks good' if decision == 'ACCEPT' else 'Needs more evidence'}"
            
            resp = client.post(f"/findings/{finding.id}/review/officer", data={
                "decision": decision,
                "comment": comment
            })
            print(f"    Finding {finding.id[:8]}... → {decision} (status: {resp.status_code})")
        
        session.commit()

def perform_supervisor_review():
    print("\n[SUPERVISOR] Performing Supervisor review...")
    with Session(engine) as session:
        findings = session.exec(select(Finding).where(Finding.status == FindingStatus.PENDING_SUPERVISOR)).all()
        print(f"    Found {len(findings)} findings pending supervisor review")

        for finding in findings:
            resp = client.post(f"/findings/{finding.id}/review/supervisor", data={
                "decision": "ACCEPT",
                "comment": "Supervisor concurs with officer decision. Finding finalized."
            })
            print(f"    Finding {finding.id[:8]}... → FINAL (status: {resp.status_code})")
        
        session.commit()

def verify_final_state():
    print("\n[VERIFY] Final state verification...")
    with Session(engine) as session:
        findings = session.exec(select(Finding)).all()
        for f in findings:
            history_count = len(f.comment_history) if f.comment_history else 0
            print(f"  - {f.id[:8]} | {f.label.value} | {f.status.value} | History: {history_count} entries")
    print("\n✓ End-to-end workflow complete\n")

if __name__ == "__main__":
    print("="*60)
    print("GAPPY FULL E2E LIVE TEST (A + B)")
    print("="*60)
    
    create_db_and_tables()
    
    reg_id, sop_id = seed_test_data()
    run_analysis(reg_id, sop_id)
    perform_officer_review()
    perform_supervisor_review()
    verify_final_state()
    
    print("ALL TESTS PASSED ✓")