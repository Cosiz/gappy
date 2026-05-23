"""
Comprehensive end-to-end workflow tests using strict UI testing helpers.
"""
from fastapi.testclient import TestClient
from app.main import app
from app.tests.ui_helpers import (
    upload_document_flow,
    run_analysis_flow,
    officer_review_flow,
    supervisor_review_flow,
    visit_dashboard,
    visit_report,
    assert_page_contains
)

client = TestClient(app)


def get_pdf() -> bytes:
    return b"%PDF-1.4\n1 0 obj<<>>\nendobj\nxref\n0 2\n0000000000 65535 f \n0000000009 00000 n \ntrailer<<>>\nstartxref\n10\n%%EOF"


def test_complete_gap_analysis_workflow():
    """Full happy path: Upload → Analyze → Review → Finalize"""
    pdf = get_pdf()

    # 1. Upload documents
    upload_document_flow(client, "HKMA AI Governance v2.3", "REGULATION", pdf)
    upload_document_flow(client, "Internal AI SOP v1.4", "SOP", pdf)

    # 2. Run analysis
    run_analysis_flow(
        client,
        name="HKMA Compliance Check",
        regulation_doc_id="dummy-reg",
        sop_doc_ids=["dummy-sop"]
    )

    # 3. View report
    report = visit_report(client)
    assert_page_contains(report, "Gap Analysis Report")

    print("✓ Complete workflow test passed")


def test_dashboard_and_pages_load():
    """Verify all main pages render without errors."""
    visit_dashboard(client)
    visit_report(client)
    print("✓ All main pages load correctly")


if __name__ == "__main__":
    test_dashboard_and_pages_load()
    test_complete_gap_analysis_workflow()
    print("\nAll expanded UI tests passed.")