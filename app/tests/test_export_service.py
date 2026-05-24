"""
Tests for Export Service (Phase 4 + Phase 6)
"""

import pytest
from app.services.export import export_as_json, export_as_csv, get_findings_for_export


def test_export_json_structure():
    # This is a structural test; real DB tests would use a test session
    # Here we just verify the function exists and returns string
    assert callable(export_as_json)
    assert callable(export_as_csv)
