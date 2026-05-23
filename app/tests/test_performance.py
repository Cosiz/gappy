"""
Performance and load testing using UI helpers.
"""
from fastapi.testclient import TestClient
from app.main import app
from app.tests.ui_helpers import (
    measure_response_time,
    assert_response_time,
    stress_test_endpoint,
    run_concurrent_uploads,
)

client = TestClient(app)


def test_page_load_times():
    """Verify key pages load reasonably fast."""
    pages = ["/dashboard", "/upload", "/report", "/run-analysis"]

    for page in pages:
        duration = measure_response_time(client, page)
        print(f"  {page}: {duration:.3f}s")

    # Assert main pages load under 2 seconds
    for page in pages:
        assert_response_time(client, page, max_seconds=2.0)

    print("✓ All pages load within acceptable time")


def test_stress_report_page():
    """Stress test the report page."""
    result = stress_test_endpoint(client, "/report", iterations=8)
    print(f"Report stress test: {result}")
    assert result["errors"] == 0, "Report page should not error under load"
    print("✓ Report page handles repeated requests")


def test_concurrent_uploads():
    """Test uploading multiple documents in sequence."""
    result = run_concurrent_uploads(client, count=4)
    print(f"Concurrent upload result: {result}")
    assert result["success_rate"] >= 75, "Most uploads should succeed"
    print("✓ Concurrent uploads handled")


if __name__ == "__main__":
    test_page_load_times()
    test_stress_report_page()
    test_concurrent_uploads()
    print("\nAll performance tests passed.")