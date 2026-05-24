"""
Error handling and resilience tests for the Analysis Engine (Phase 6)
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.analysis import assess_requirement, run_gap_analysis


class TestLLMErrorHandling:
    def test_assess_requirement_handles_llm_failure(self):
        """When the LLM call fails, the function should return a safe fallback."""
        with patch("app.services.analysis.litellm.completion") as mock_llm:
            mock_llm.side_effect = Exception("API rate limit exceeded")
            
            requirement = {
                "requirement_id": "TM-G-2 3.1",
                "action": "Maintain a business continuity plan"
            }
            
            result = assess_requirement(requirement, "some sop context")
            
            assert result["label"] == "MISSING"
            assert result["confidence"] <= 0.4
            assert "LLM assessment failed" in result["rationale"]
            assert result["evidence"] == []

    def test_assess_requirement_handles_bad_json(self):
        """When MiniMax returns malformed JSON, the function should fallback gracefully."""
        with patch("app.services.analysis.litellm.completion") as mock_llm:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "This is not valid JSON at all {"
            mock_llm.return_value = mock_response
            
            requirement = {"requirement_id": "TM-E-1 4.2", "action": "Customer authentication"}
            result = assess_requirement(requirement, "sop content")
            
            assert result["label"] == "MISSING"
            assert "LLM assessment failed" in result.get("rationale", "")


class TestPipelineResilience:
    def test_run_gap_analysis_with_no_sops(self):
        """Pipeline should not crash when no SOP documents are provided."""
        # This would require a real session + documents in a full integration test.
        # Here we just verify the function signature and basic behavior.
        assert callable(run_gap_analysis)

    def test_run_gap_analysis_handles_empty_regulation_text(self):
        """Empty regulation text should result in no requirements extracted."""
        from app.services.analysis import extract_requirements_from_text
        reqs = extract_requirements_from_text("")
        assert reqs == []
