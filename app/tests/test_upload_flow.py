"""
Example of strict end-to-end UI testing for Gappy.
These tests simulate real user actions and verify visible outcomes.
"""
from fastapi.testclient import TestClient
from app.main import app
from app.tests.ui_helpers import upload_document_flow, assert_page_contains

client = TestClient(app)


def test_upload_regulation_shows_success():
    """User uploads a regulation and should see clear success confirmation."""
    pdf = b"%PDF-1.4\n1 0 obj<<>>\nendobj\nxref\n0 2\n0000000000 65535 f \n0000000009 00000 n \ntrailer<<>>\nstartxref\n10\n%%EOF"

    response = upload_document_flow(
        client,
        title="HKMA AI Governance v2.3",
        doc_type="REGULATION",
        file_content=pdf
    )

    # Extra verification: user should see link to report
    assert_page_contains(response, "View in Report")


def test_upload_sop_shows_success():
    """User uploads an SOP and should see success banner."""
    pdf = b"%PDF-1.4\n1 0 obj<<>>\nendobj\nxref\n0 2\n0000000000 65535 f \n0000000009 00000 n \ntrailer<<>>\nstartxref\n10\n%%EOF"

    response = upload_document_flow(
        client,
        title="Internal Risk SOP v1.4",
        doc_type="SOP",
        file_content=pdf
    )

    assert_page_contains(response, "Internal Risk SOP v1.4")


if __name__ == "__main__":
    test_upload_regulation_shows_success()
    test_upload_sop_shows_success()
    print("All UI flow tests passed.")