"""Automated test suite for Phase 5 Pre-Interface Mathematical Audit."""

from pathlib import Path
import pandas as pd
import pytest

from python.database.duckdb_manager import DuckDBManager
from python.validation.audit_phase5_mathematics import run_pre_interface_mathematical_audit

DOCS_DIR = Path("docs")

@pytest.fixture(scope="module")
def db():
    manager = DuckDBManager()
    yield manager
    manager.close()

def test_mathematical_audit_document_exists():
    """Verify that PHASE5_PRE_INTERFACE_MATHEMATICAL_AUDIT.md exists and is non-empty."""
    doc_path = DOCS_DIR / "PHASE5_PRE_INTERFACE_MATHEMATICAL_AUDIT.md"
    assert doc_path.exists()
    content = doc_path.read_text(encoding="utf-8")
    assert len(content) > 500
    assert "PASSED" in content

def test_independent_audit_discrepancies_are_zero():
    """Verify all audit results have zero discrepancy between expected and recalculated."""
    results = run_pre_interface_mathematical_audit()
    assert len(results) >= 8
    for r in results:
        assert r["status"] == "PASSED"
        assert abs(float(r["discrepancy"])) < 0.05, f"Discrepancy detected in {r['metric']}: {r['discrepancy']}"
