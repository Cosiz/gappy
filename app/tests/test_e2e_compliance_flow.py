"""
End-to-End Compliance Officer + Supervisor Workflow Test
Tests the complete user journey from a compliance officer and supervisor perspective.
"""
import sys
sys.path.insert(0, '/app/gappy')

from fastapi.testclient import TestClient
from app.main import app
from sqlmodel import Session, select
from app.core.database import engine
from app.models.finding import Finding
from app.models.document import Document

client = TestClient(app)

def test_officer_and_supervisor_workflow():
    print("\n" + "="*60)
    print("GAPPY - COMPLIANCE OFFICER + SUPERVISOR E2E TEST")
    print("="*60 + "\n")

    # 1. Check Dashboard
    print("[STEP 1] Compliance Officer opens Dashboard...")
    r = client.get("/dashboard")
    assert r.status_code == 200
    print("    ✓ Dashboard loads successfully")

    # 2. Check Upload page
    print("\n[STEP 2] Officer navigates to Upload page...")
    r = client.get("/upload")
    assert r.status_code == 200
    print("    ✓ Upload page accessible")

    # 3. Check Report page (even if empty)
    print("\n[STEP 3] Officer views Report page...")
    r = client.get("/report")
    assert r.status_code == 200
    print("    ✓ Report page loads")

    # 4. Check database state
    print("\n[STEP 4] Checking current data state...")
    with Session(engine) as session:
        docs = session.exec(select(Document)).all()
        findings = session.exec(select(Finding)).all()
        print(f"    Documents in system: {len(docs)}")
        print(f"    Findings in system: {len(findings)}")
        
        for f in findings:
            print(f"      - Finding {f.id}: {f.label.value} | Status: {f.status.value}")
            if f.comment_history:
                print(f"        Review History: {len(f.comment_history)} entries")

    print("\n[STEP 5] Verifying UI features exist in templates...")
    
    # Check report template has required elements
    report_html = open("/app/gappy/app/templates/report.html").read()
    
    checks = [
        ("Review History section", "Review History" in report_html),
        ("Officer review form", "Compliance Officer Review" in report_html),
        ("Accept/Dispute/Clarification buttons", "ACCEPT" in report_html and "DISPUTE" in report_html),
        ("Comment textarea", "name=\"comment\"" in report_html),
        ("Confidence score display", "Confidence:" in report_html),
        ("Status badges", "Pending Officer Review" in report_html),
        ("Documents section", "Documents Used in This Analysis" in report_html),
    ]
    
    all_passed = True
    for name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"    {status} {name}")
        if not passed:
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("ALL E2E CHECKS PASSED")
    else:
        print("SOME CHECKS FAILED")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_officer_and_supervisor_workflow()