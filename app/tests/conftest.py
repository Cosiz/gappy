"""
Pytest configuration and shared fixtures for Project Gappy tests (Phase 6)
"""

import pytest
from datetime import datetime, timedelta
from app.models.finding import Finding, FindingStatus, FindingLabel


@pytest.fixture
def sample_finding():
    """Create a basic pending officer finding."""
    return Finding(
        analysis_id="test-analysis-123",
        requirement_id="TM-G-2 3.1",
        label=FindingLabel.MISSING,
        confidence=0.55,
        rationale="No relevant SOP content found for this requirement.",
        status=FindingStatus.PENDING_OFFICER,
        missing_aspects=["Test aspect"],
        evidence=[],
        supporting_anchors=[],
    )


@pytest.fixture
def covered_finding():
    """Create a covered finding with evidence."""
    return Finding(
        analysis_id="test-analysis-123",
        requirement_id="TM-E-1 3.3",
        label=FindingLabel.COVERED,
        confidence=0.82,
        rationale="SOP-04 fully addresses penetration testing requirements.",
        status=FindingStatus.PENDING_OFFICER,
        missing_aspects=[],
        evidence=["SOP-04 §2.1: 'External penetration test conducted every 24 months'"],
        supporting_anchors=["SOP-04 §2.1"],
    )


@pytest.fixture
def pending_supervisor_finding(sample_finding):
    """Finding that has been accepted by officer."""
    f = sample_finding
    f.status = FindingStatus.PENDING_SUPERVISOR
    f.undo_until = datetime.utcnow() + timedelta(minutes=25)
    return f


@pytest.fixture
def final_finding(sample_finding):
    """Finding that has reached final state."""
    f = sample_finding
    f.status = FindingStatus.FINAL
    return f
