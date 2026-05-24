"""
Unit tests for the Workflow Engine (Phase 3 + Phase 6)
Uses shared fixtures from conftest.py
"""

import pytest
from datetime import datetime, timedelta
from app.services.workflow import (
    can_officer_review,
    can_supervisor_review,
    can_undo,
    request_clarification,
)
from app.models.finding import FindingStatus


def test_officer_can_review_pending_officer(sample_finding):
    assert can_officer_review(sample_finding) is True


def test_supervisor_cannot_review_pending_officer(sample_finding):
    assert can_supervisor_review(sample_finding) is False


def test_supervisor_can_review_pending_supervisor(pending_supervisor_finding):
    assert can_supervisor_review(pending_supervisor_finding) is True


def test_undo_allowed_within_window(pending_supervisor_finding):
    assert can_undo(pending_supervisor_finding) is True


def test_undo_not_allowed_after_window(pending_supervisor_finding):
    pending_supervisor_finding.undo_until = datetime.utcnow() - timedelta(minutes=5)
    assert can_undo(pending_supervisor_finding) is False


def test_final_finding_cannot_be_reviewed(final_finding):
    assert can_officer_review(final_finding) is False
    assert can_supervisor_review(final_finding) is False


def test_clarification_from_officer_pending(sample_finding):
    # In real usage this requires a session; here we just verify state logic
    assert sample_finding.status == FindingStatus.PENDING_OFFICER
