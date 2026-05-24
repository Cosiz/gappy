"""
Performance and stress tests (Phase 6)

These tests are meant to be run manually or in CI with larger datasets.
"""

import pytest
import time
from app.services.analysis import chunk_text, retrieve_relevant_chunks


def test_chunking_performance():
    """Chunking 50k characters should be fast."""
    large_text = "Business continuity planning is critical. " * 5000
    start = time.time()
    chunks = chunk_text(large_text, max_chars=800, overlap=100)
    duration = time.time() - start
    
    assert len(chunks) > 50
    assert duration < 2.0, f"Chunking took too long: {duration:.2f}s"


def test_retrieval_scales_reasonably():
    """Retrieval should handle moderately large SOP contexts."""
    requirement = {"action": "risk assessment and penetration testing"}
    large_context = ("Risk assessment procedures and penetration testing requirements. " * 2000)
    
    start = time.time()
    chunks = retrieve_relevant_chunks(requirement, large_context, top_k=5)
    duration = time.time() - start
    
    assert duration < 3.0
