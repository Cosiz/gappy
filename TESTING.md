# Testing Guide — Project Gappy (Phase 6)

This document describes how to run and extend the test suite.

## Running Tests

### Prerequisites
Make sure you have the development dependencies installed:

```bash
pip install -e ".[dev]"   # or pip install pytest pytest-mock
```

### Run All Tests

```bash
pytest app/tests/ -v
```

### Run Specific Test Files

```bash
pytest app/tests/test_analysis_pipeline.py -v
pytest app/tests/test_workflow_engine.py -v
pytest app/tests/test_error_handling.py -v
```

### Run With Coverage

```bash
pytest app/tests/ --cov=app --cov-report=html
```

## Test Organization

| File                              | Focus Area                              | Key Fixtures Used |
|-----------------------------------|-----------------------------------------|-------------------|
| `test_analysis_pipeline.py`       | Requirement extraction, chunking, retrieval, confidence scoring | — |
| `test_workflow_engine.py`         | Officer/Supervisor permissions, undo window, clarification | `sample_finding`, `pending_supervisor_finding`, `final_finding` |
| `test_error_handling.py`          | LLM failures, bad JSON responses, resilience | Mocked `litellm.completion` |
| `test_export_service.py`          | Export structure (JSON/CSV/PDF)         | — |
| `test_performance.py`             | Chunking and retrieval performance      | — |
| `conftest.py`                     | Shared fixtures                         | All test files |

## Writing New Tests

### Using Fixtures

```python
def test_something(covered_finding):
    assert covered_finding.label.value == "COVERED"
    assert covered_finding.confidence > 0.7
```

### Mocking the LLM

```python
from unittest.mock import patch, MagicMock

def test_llm_failure():
    with patch("app.services.analysis.litellm.completion") as mock:
        mock.side_effect = Exception("Rate limit")
        # test fallback behavior
```

### Adding New Fixtures

Add new fixtures to `conftest.py` when they are used across multiple test files.

## Continuous Integration

In CI, run:

```bash
pytest app/tests/ --tb=short -q
```

Consider adding:

- `--cov=app --cov-fail-under=70`
- Integration tests against a test PostgreSQL instance

## Known Limitations

- Full end-to-end tests require a database and MiniMax API key.
- Some tests currently use mocks for LLM calls.
- Performance tests are best run manually with larger document sets.

## Next Steps (Future Hardening)

- [ ] Add integration tests using `TestClient` + in-memory SQLite
- [ ] Add property-based testing for requirement extraction
- [ ] Add load tests for the analysis pipeline
- [ ] Improve coverage of `run_gap_analysis` end-to-end flow
