"""Provenance Tracker and Surrogate Key Generator."""

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Union, Optional

from python.config import Settings
from python.models.canonical import SourceProvenance
from python.models.enums import SourceType, SourceProvider


def generate_id(prefix: str) -> str:
    """Generate a stable, uppercase unique identifier with entity prefix."""
    unique_part = uuid.uuid4().hex[:12].upper()
    return f"{prefix.upper()}_{unique_part}"


def compute_file_sha256(file_path: Union[str, Path]) -> str:
    """Compute SHA-256 checksum of a file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found for hash calculation: {path}")

    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def compute_content_sha256(content: Union[str, bytes]) -> str:
    """Compute SHA-256 of string or bytes content."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


class ProvenanceTracker:
    """Creates and tracks source provenance records for all ingested files."""

    def __init__(self, pipeline_version: Optional[str] = None):
        self.pipeline_version = pipeline_version or Settings.PIPELINE_VERSION

    def create_provenance(
        self,
        source_type: SourceType,
        source_provider: Union[SourceProvider, str],
        source_file_path: Union[str, Path],
        parser_version: str = "1.0.0",
        file_hash: Optional[str] = None,
    ) -> SourceProvenance:
        """Generate a new SourceProvenance model."""
        path = Path(source_file_path)
        path_str = path.as_posix()
        
        if file_hash is None:
            if path.exists():
                file_hash = compute_file_sha256(path)
            else:
                file_hash = compute_content_sha256(path_str)

        provider_str = source_provider.value if isinstance(source_provider, SourceProvider) else str(source_provider)

        return SourceProvenance(
            provenance_id=generate_id("PRV"),
            source_type=source_type,
            source_provider=provider_str,
            source_file_path=path_str,
            source_file_hash=file_hash,
            parser_version=parser_version,
            pipeline_version=self.pipeline_version,
            ingestion_timestamp=datetime.now(timezone.utc),
        )
