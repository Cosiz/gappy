"""
Unit tests for the Analysis Engine (Phase 2 + Phase 6)

Tests the structured pipeline functions.
"""

import pytest
from app.services.analysis import (
    extract_requirements_from_text,
    chunk_text,
    retrieve_relevant_chunks,
    compute_confidence_score,
    validate_citations
)


def test_extract_requirements_basic():
    text = """
    3.1 The bank shall maintain a business continuity plan.
    3.2 Senior management should review the plan annually.
    """
    reqs = extract_requirements_from_text(text)
    assert len(reqs) >= 1
    assert any("business continuity" in r["action"].lower() for r in reqs)


def test_chunk_text():
    text = "a" * 2000
    chunks = chunk_text(text, max_chars=500, overlap=50)
    assert len(chunks) > 2
    assert all(len(c) <= 550 for c in chunks)


def test_retrieve_relevant_chunks():
    requirement = {"action": "business continuity planning and alternate sites"}
    sop_context = """
    === SOP-12 ===
    The bank maintains an alternate business site in Kowloon East.
    Business continuity plans are reviewed annually.
    """
    chunks = retrieve_relevant_chunks(requirement, sop_context, top_k=3)
    assert len(chunks) >= 1
    assert any("alternate" in c.lower() or "continuity" in c.lower() for c in chunks)


def test_compute_confidence_score():
    assessment = {
        "label": "COVERED",
        "confidence": 0.85,
        "evidence": ["SOP-12 §4.1: 'Dedicated alternate site'"]
    }
    requirement = {"action": "alternate sites"}
    retrieved = ["Dedicated alternate site in Kowloon East with 24/7 access"]
    validated = ["SOP-12 §4.1: 'Dedicated alternate site'"]
    
    score = compute_confidence_score(assessment, requirement, retrieved, validated)
    assert 0.6 <= score <= 0.98


def test_validate_citations():
    assessment = {
        "evidence": ["SOP-12 §4.1: 'Dedicated alternate site'"],
        "confidence": 0.8
    }
    chunks = ["The bank maintains a dedicated alternate business site in Kowloon East"]
    
    result = validate_citations(assessment, chunks)
    assert len(result["evidence"]) == 1
    assert result["confidence"] >= 0.6
