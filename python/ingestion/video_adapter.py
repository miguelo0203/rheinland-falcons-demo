"""Video and Synchronization Ingestion Adapter."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from python.ingestion.base import BaseAdapter, NormalizedPayload
from python.ingestion.provenance import compute_file_sha256, generate_id
from python.models.canonical import Video, VideoEventSync
from python.models.enums import SourceType


class VideoAdapter(BaseAdapter):
    """Adapter for ingesting video files and associated synchronization metadata."""

    def __init__(
        self,
        provider_name: str = "VIDEO_METADATA",
        entity_resolver=None,
        provenance_tracker=None,
    ):
        super().__init__(
            source_type=SourceType.VIDEO,
            provider_name=provider_name,
            entity_resolver=entity_resolver,
            provenance_tracker=provenance_tracker,
        )

    def detect(self, file_path: Union[str, Path]) -> bool:
        """Detect if file is a video or video metadata JSON."""
        path = Path(file_path)
        if not path.exists():
            return False
        if path.suffix.lower() in [".mp4", ".mkv", ".mov", ".avi"]:
            return True
        if path.suffix.lower() == ".json":
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return "video" in data or "video_id" in data or "duration_seconds" in data or "sync_tags" in data
            except Exception:
                return False
        return False

    def extract(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Extract metadata and sync tags."""
        path = Path(file_path)
        if path.suffix.lower() == ".json":
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            # Direct video media file
            file_size = path.stat().st_size
            sha256 = compute_file_sha256(path)
            return {
                "file_path": path.as_posix(),
                "file_size_bytes": file_size,
                "checksum_sha256": sha256,
                "container_format": path.suffix.lstrip(".").lower(),
                "duration_seconds": None,
                "sync_tags": [],
            }

    def normalize(
        self,
        raw_data: Dict[str, Any],
        file_path: Union[str, Path],
        game_id: Optional[str] = None,
        season_id: Optional[str] = None,
        competition_id: Optional[str] = None,
    ) -> NormalizedPayload:
        """Normalize video record and synchronization anchors."""
        provenance = self.provenance_tracker.create_provenance(
            source_type=SourceType.VIDEO,
            source_provider=self.provider_name,
            source_file_path=file_path,
            parser_version="1.0.0",
        )

        payload = NormalizedPayload(provenance=provenance)
        actual_game_id = game_id or raw_data.get("game_id") or generate_id("GAM")
        video_id = raw_data.get("video_id") or generate_id("VID")

        path_str = raw_data.get("file_path") or Path(file_path).as_posix()
        checksum = raw_data.get("checksum_sha256")
        if not checksum:
            if Path(file_path).exists():
                checksum = compute_file_sha256(file_path)
            else:
                checksum = "0000000000000000000000000000000000000000000000000000000000000000"

        vid_record = Video(
            video_id=video_id,
            game_id=actual_game_id,
            file_path=path_str,
            duration_seconds=raw_data.get("duration_seconds"),
            container_format=raw_data.get("container_format", Path(file_path).suffix.lstrip(".")),
            codec=raw_data.get("codec"),
            resolution_width=raw_data.get("resolution_width"),
            resolution_height=raw_data.get("resolution_height"),
            fps=raw_data.get("fps"),
            file_size_bytes=raw_data.get("file_size_bytes"),
            checksum_sha256=checksum,
            camera_angle=raw_data.get("camera_angle"),
        )
        payload.videos.append(vid_record)

        # Process sync anchors if present (supports both PBP -> Video and Video Observation -> Event)
        for sync in raw_data.get("sync_tags", []):
            sync_record = VideoEventSync(
                sync_id=generate_id("SYN"),
                event_id=sync.get("event_id"),
                game_id=actual_game_id,
                video_id=video_id,
                video_start_time_s=float(sync.get("start_s", 0.0)),
                video_end_time_s=float(sync.get("end_s", 0.0)),
                confidence_level=sync.get("confidence", "HIGH"),
                sync_method=sync.get("method", "MANUAL"),
                verified_by=sync.get("verified_by"),
            )
            payload.video_event_syncs.append(sync_record)

        return payload
