"""
UI Testing Helpers for Gappy

These helpers enforce end-to-end browser-style testing:
- Always follow redirects after form submissions
- Check for visible success indicators in the final page
- Treat "API returns 200" as insufficient — user must see confirmation
"""
import time
from typing import Optional, Dict, Any, List, Callable
from fastapi.testclient import TestClient


# =============================================================================
# Core Helpers
# =============================================================================

def submit_form(
    client: TestClient,
    url: str,
    data: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    follow_redirects: bool = True
) -> Any:
    response = client.post(
        url,
        data=data or {},
        files=files or {},
        follow_redirects=follow_redirects
    )
    return response


def visit_page(client: TestClient, url: str) -> Any:
    response = client.get(url)
    assert_status(response, 200)
    return response


def assert_success_banner(response: Any, expected_text: Optional[str] = None) -> bool:
    content = response.text.lower()
    success_indicators = [
        "successfully", "uploaded successfully", "created successfully",
        "saved successfully", "document uploaded", "analysis completed",
        "review submitted", "decision recorded",
    ]
    if expected_text:
        success_indicators.append(expected_text.lower())

    if not any(indicator in content for indicator in success_indicators):
        raise AssertionError(
            f"Expected success banner in response. Snippet: {response.text[:300]}..."
        )
    return True


def assert_error_message(response: Any, expected_text: Optional[str] = None) -> bool:
    content = response.text.lower()
    error_indicators = ["error", "invalid", "failed", "not found", "required", "missing"]

    if expected_text:
        error_indicators.append(expected_text.lower())

    if not any(indicator in content for indicator in error_indicators):
        raise AssertionError(
            f"Expected error message but none found. Snippet: {response.text[:300]}..."
        )
    return True


def assert_page_contains(response: Any, text: str) -> bool:
    if text not in response.text:
        raise AssertionError(
            f"Expected '{text}' in page. Snippet: {response.text[:400]}..."
        )
    return True


def assert_status(response: Any, expected_status: int) -> bool:
    if response.status_code != expected_status:
        raise AssertionError(
            f"Expected status {expected_status}, got {response.status_code}. "
            f"Response: {response.text[:300]}"
        )
    return True


# =============================================================================
# Page Helpers
# =============================================================================

def visit_dashboard(client: TestClient) -> Any:
    return visit_page(client, "/dashboard")


def visit_upload_page(client: TestClient) -> Any:
    return visit_page(client, "/upload")


def visit_report(client: TestClient) -> Any:
    return visit_page(client, "/report")


# =============================================================================
# Positive Flows
# =============================================================================

def upload_document_flow(
    client: TestClient,
    title: str,
    doc_type: str,
    file_content: bytes,
    filename: str = "test.pdf"
) -> Any:
    files = {"file": (filename, file_content, "application/pdf")}
    data = {"title": title, "doc_type": doc_type}

    response = submit_form(client, "/documents/upload", data=data, files=files)
    assert_status(response, 200)
    assert_success_banner(response, "uploaded successfully")
    assert_page_contains(response, title)
    return response


def run_analysis_flow(
    client: TestClient,
    name: str,
    regulation_doc_id: str,
    sop_doc_ids: List[str]
) -> Any:
    response = client.post("/analyses/run", json={
        "name": name,
        "regulation_doc_id": regulation_doc_id,
        "sop_doc_ids": sop_doc_ids
    })
    assert_status(response, 200)
    result = response.json()
    if result.get("status") != "completed":
        raise AssertionError(f"Analysis failed: {result}")
    return response


def officer_review_flow(
    client: TestClient,
    finding_id: str,
    decision: str = "ACCEPT",
    comment: str = "Looks good"
) -> Any:
    response = submit_form(
        client,
        f"/findings/{finding_id}/review/officer",
        data={"decision": decision, "comment": comment}
    )
    assert_status(response, 200)
    assert_success_banner(response, "success")
    return response


def supervisor_review_flow(
    client: TestClient,
    finding_id: str,
    decision: str = "ACCEPT",
    comment: str = "Approved"
) -> Any:
    response = submit_form(
        client,
        f"/findings/{finding_id}/review/supervisor",
        data={"decision": decision, "comment": comment}
    )
    assert_status(response, 200)
    assert_success_banner(response, "success")
    return response


# =============================================================================
# Negative / Error Test Helpers
# =============================================================================

def upload_without_file(client: TestClient, title: str = "No File", doc_type: str = "REGULATION") -> Any:
    data = {"title": title, "doc_type": doc_type}
    response = client.post("/documents/upload", data=data)
    return response


def upload_without_title(client: TestClient, file_content: bytes, doc_type: str = "REGULATION") -> Any:
    files = {"file": ("test.pdf", file_content, "application/pdf")}
    data = {"doc_type": doc_type}
    response = client.post("/documents/upload", data=data, files=files)
    return response


def upload_invalid_file_type(client: TestClient, title: str = "Bad File", doc_type: str = "REGULATION") -> Any:
    files = {"file": ("malware.exe", b"MZ\x90\x00", "application/x-msdownload")}
    data = {"title": title, "doc_type": doc_type}
    response = client.post("/documents/upload", data=data, files=files)
    return response


def upload_very_large_file(client: TestClient, title: str = "Huge File", doc_type: str = "REGULATION") -> Any:
    large_content = b"%PDF-1.4 " + (b"x" * (10 * 1024 * 1024))
    files = {"file": ("huge.pdf", large_content, "application/pdf")}
    data = {"title": title, "doc_type": doc_type}
    response = client.post("/documents/upload", data=data, files=files)
    return response


def submit_invalid_officer_decision(client: TestClient, finding_id: str) -> Any:
    response = submit_form(
        client,
        f"/findings/{finding_id}/review/officer",
        data={"decision": "INVALID_DECISION", "comment": "test"}
    )
    return response


def access_nonexistent_finding(client: TestClient) -> Any:
    return client.get("/findings/nonexistent-id-12345")


# =============================================================================
# Performance & Load Testing Helpers
# =============================================================================

def measure_response_time(client: TestClient, url: str, method: str = "GET", **kwargs) -> float:
    """Measure how long a request takes (in seconds)."""
    start = time.time()
    if method.upper() == "GET":
        client.get(url, **kwargs)
    elif method.upper() == "POST":
        client.post(url, **kwargs)
    return time.time() - start


def assert_response_time(client: TestClient, url: str, max_seconds: float = 1.0) -> float:
    """Assert that a page loads within acceptable time."""
    duration = measure_response_time(client, url)
    if duration > max_seconds:
        raise AssertionError(
            f"Page {url} took {duration:.2f}s (max allowed: {max_seconds}s)"
        )
    return duration


def stress_test_endpoint(
    client: TestClient,
    url: str,
    iterations: int = 10,
    method: str = "GET",
    **kwargs
) -> Dict[str, Any]:
    """
    Run the same request multiple times and return performance stats.
    """
    times = []
    errors = 0

    for _ in range(iterations):
        try:
            start = time.time()
            if method.upper() == "GET":
                resp = client.get(url, **kwargs)
            else:
                resp = client.post(url, **kwargs)

            if resp.status_code >= 400:
                errors += 1
            times.append(time.time() - start)
        except Exception:
            errors += 1

    if times:
        avg = sum(times) / len(times)
        max_t = max(times)
        min_t = min(times)
    else:
        avg = max_t = min_t = 0

    return {
        "iterations": iterations,
        "errors": errors,
        "avg_time": round(avg, 3),
        "max_time": round(max_t, 3),
        "min_time": round(min_t, 3),
    }


def run_concurrent_uploads(
    client: TestClient,
    count: int = 5,
    title_prefix: str = "Load Test"
) -> Dict[str, Any]:
    """
    Simulate multiple document uploads in sequence.
    Returns success rate and timing.
    """
    pdf = b"%PDF-1.4 test content"
    successes = 0
    times = []

    for i in range(count):
        start = time.time()
        try:
            resp = client.post(
                "/documents/upload",
                data={"title": f"{title_prefix} {i}", "doc_type": "REGULATION"},
                files={"file": (f"test{i}.pdf", pdf, "application/pdf")},
                follow_redirects=True
            )
            if resp.status_code == 200:
                successes += 1
            times.append(time.time() - start)
        except Exception:
            pass

    return {
        "total": count,
        "successes": successes,
        "success_rate": round(successes / count * 100, 1) if count > 0 else 0,
        "avg_time": round(sum(times) / len(times), 3) if times else 0,
    }