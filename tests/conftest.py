"""Pytest configuration and shared fixtures for Sandbox tests."""

import pytest
from pathlib import Path
import tempfile
import shutil

from python.database.duckdb_manager import DuckDBManager
from python.ingestion.entity_resolver import EntityResolver
from python.ingestion.provenance import ProvenanceTracker
from python.ingestion.conflict_detector import ConflictDetector
from python.synthetic.generate_samples import generate_all_permutations


@pytest.fixture(scope="session")
def synthetic_manifest():
    """Generate synthetic test files for test session."""
    return generate_all_permutations()


@pytest.fixture
def temp_duckdb():
    """Provide an in-memory DuckDB manager initialized with canonical DDL."""
    manager = DuckDBManager(in_memory=True)
    manager.initialize_schema()
    yield manager
    manager.close()


@pytest.fixture
def entity_resolver():
    """Fresh entity resolver."""
    return EntityResolver()


@pytest.fixture
def provenance_tracker():
    """Fresh provenance tracker."""
    return ProvenanceTracker(pipeline_version="1.0.0")


@pytest.fixture
def conflict_detector():
    """Fresh conflict detector."""
    return ConflictDetector()
