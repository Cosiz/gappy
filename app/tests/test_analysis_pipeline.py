"""
Unit tests for the Analysis Engine (Phase 2 + Phase 6)
"""

import pytest
from app.services.analysis import (
    extract_requirements_from_text,
    chunk_text,
    retrieve_relevant_chunks,
    compute_confidence_score,
    validate_citations,
)


class TestRequirementExtraction:
    def test_extracts_shall_requirements(self):
        text = "2.1 The bank shall maintain adequate risk controls."
        reqs = extract_requirements_from_text(text)
        assert len(reqs) >= 1
        assert reqs[0]["obligation_type"] == "shall"

    def test_extracts_should_requirements(self):
        text = "4.2 Senior management should review policies annually."
        reqs = extract_requirements_from_text(text)
        assert any(r["obligation_type"] == "should" for r in reqs)

    def test_ignores_short_sections(self):
        text = "1.0 Short."
        reqs = extract_requirements_from_text(text)
        assert len(reqs) == 0


class TestChunkingAndRetrieval:
    def test_chunk_text_creates_overlapping_chunks(self):
        text = "x" * 1500
        chunks = chunk_text(text, max_chars=400, overlap=50)
        assert len(chunks) >= 3

    def test_retrieve_relevant_chunks_prefers_overlap(self):
        requirement = {"action": "alternate business continuity site"}
        sop_context = "The bank maintains a dedicated alternate site in Kowloon East for business continuity."
        chunks = retrieve_relevant_chunks(requirement, sop_context, top_k=3)
        assert len(chunks) > 0


class TestConfidenceScoring:
    def test_high_confidence_for_covered_with_good_evidence(self):
        assessment = {
            "label": "COVERED",
            "confidence": 0.9,
            "evidence": ["SOP-12 §4.1: 'Dedicated alternate site'"]
        }
        req = {"action": "alternate sites"}
        retrieved = ["Dedicated alternate site in Kowloon East"]
        validated = ["SOP-12 §4.1: 'Dedicated alternate site'"]
        
        score = compute_confidence_score(assessment, req, retrieved, validated)
        assert score > 0.75

    def test_low_confidence_for_missing(self):
        assessment = {"label": "MISSING", "confidence": 0.3, "evidence": []}
        req = {"action": "public relations strategy"}
        retrieved = []
        validated = []
        
        score = compute_confidence_score(assessment, req, retrieved, validated)
        assert score < 0.6


class TestCitationValidation:
    def test_validates_matching_evidence(self):
        assessment = {
            "evidence": ["SOP-12 §4.1: 'Dedicated alternate site'"],
            "confidence": 0.7
        }
        chunks = ["The bank maintains a dedicated alternate business site in Kowloon East"]
        
        result = validate_citations(assessment, chunks)
        assert len(result["evidence"]) == 1
        assert result["confidence"] > 0.6

    def test_reduces_confidence_on_poor_validation(self):
        assessment = {
            "evidence": ["SOP-99 §1.0: 'Nonexistent text'"],
            "confidence": 0.8
        }
        chunks = ["Completely different content here"]
        
        result = validate_citations(assessment, chunks)
        assert result["confidence"] < 0.7
