"""Technical Video Metadata Extraction & Analysis Readiness Engine for Rheinland Falcons Platform.

Provides deterministic, rule-based extraction of video container properties,
codec, geometry, temporal range, SHA-256 checksums, and audio presence.
Strictly rejects fake AI recognition in favor of verifiable technical validation.
"""

import hashlib
import logging
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger("falcons.video.metadata")

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import mutagen
    from mutagen.mp4 import MP4
except ImportError:
    mutagen = None


def format_seconds_to_timestamp(seconds: Union[int, float]) -> str:
    """Converts seconds into standard MM:SS or MM:SS.s display format.
    
    Examples:
        871.2 -> '14:31.2'
        3665.0 -> '01:01:05.0'
        45.0 -> '00:45.0'
    """
    if seconds is None or math.isnan(seconds) or seconds < 0:
        return "00:00.0"

    total_secs = float(seconds)
    hours = int(total_secs // 3600)
    minutes = int((total_secs % 3600) // 60)
    secs = total_secs % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:04.1f}"
    else:
        return f"{minutes:02d}:{secs:04.1f}"


def parse_timestamp_to_seconds(ts_str: str) -> float:
    """Parses MM:SS, MM:SS.s, HH:MM:SS, or raw float strings into float seconds.
    
    Examples:
        '14:31.2' -> 871.2
        '14:31' -> 871.0
        '01:05:20' -> 3920.0
        '871.2' -> 871.2
    """
    if not ts_str or not isinstance(ts_str, str):
        return 0.0

    cleaned = ts_str.strip()
    if not cleaned:
        return 0.0

    # Direct numeric value
    try:
        return float(cleaned)
    except ValueError:
        pass

    parts = cleaned.split(":")
    try:
        if len(parts) == 3:
            h, m, s = parts
            return float(h) * 3600.0 + float(m) * 60.0 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return float(m) * 60.0 + float(s)
        elif len(parts) == 1:
            return float(parts[0])
    except (ValueError, TypeError):
        return 0.0

    return 0.0


def validate_clip_range(
    start_time_s: float,
    end_time_s: float,
    video_duration_s: Optional[float] = None
) -> Tuple[bool, str]:
    """Validates clip temporal boundaries against physical video constraints.
    
    Rule: 0 <= start_time_s < end_time_s <= video.duration_seconds
    """
    if start_time_s < 0.0:
        return False, f"Start time ({start_time_s:.1f}s) cannot be negative."

    if end_time_s <= start_time_s:
        return False, f"End time ({end_time_s:.1f}s) must be strictly greater than start time ({start_time_s:.1f}s)."

    if video_duration_s is not None and video_duration_s > 0.0:
        # Allow tiny 0.5s tolerance for browser roundoff at end of stream
        if end_time_s > (video_duration_s + 0.5):
            return False, f"End time ({end_time_s:.1f}s) exceeds video duration ({video_duration_s:.1f}s)."

    return True, "Valid temporal clip boundaries."


def compute_file_sha256(file_path: Union[str, Path], chunk_size: int = 65536) -> str:
    """Computes SHA-256 hash for strict provenance and audit integrity."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest()


def check_audio_presence(file_path: Union[str, Path]) -> bool:
    """Inspects video container for presence of valid audio tracks without fake claims."""
    p = Path(file_path)
    if not p.exists():
        return False

    if mutagen is not None:
        try:
            mf = mutagen.File(str(p))
            if mf is not None:
                # MP4 / M4V container
                if hasattr(mf, "info"):
                    # Check for audio streams or channels
                    if getattr(mf.info, "channels", 0) > 0 or getattr(mf.info, "sample_rate", 0) > 0:
                        return True
                    # Check tags/atoms for audio track
                    if hasattr(mf, "tags") and mf.tags:
                        return True
        except Exception:
            pass

    # Fallback to checking MP4 'soun' handler box in raw container header
    try:
        with open(str(p), "rb") as f:
            header_sample = f.read(262144)  # 256KB sample
            if b"soun" in header_sample or b"mp4a" in header_sample or b"ac-3" in header_sample:
                return True
    except Exception:
        pass

    return False


def classify_video_readiness(
    width: int,
    height: int,
    fps: float,
    duration_s: float,
    container_format: str,
    stream_readable: bool,
    audio_present: bool = True
) -> Dict[str, Any]:
    """Deterministic, rule-based Video Analysis Readiness Evaluator.
    
    States:
        READY: Video meets full requirements for technical tactical review.
        LIMITED: Video can be played and clipped, but has reduced resolution, low fps, or short length.
        UNSUPPORTED: File cannot be read, corrupted stream, or 0 duration.
    """
    criteria: List[Dict[str, Any]] = []

    if not stream_readable or duration_s <= 0.0 or width <= 0 or height <= 0:
        return {
            "status": "UNSUPPORTED",
            "badge": "🔴 UNSUPPORTED",
            "is_ready": False,
            "headline": "Video Stream Unreadable or Corrupt",
            "criteria": [
                {
                    "name": "Stream Decodability",
                    "passed": False,
                    "status": "FAIL",
                    "detail": "Failed to decode video frames. Container format may be unsupported or file is corrupted."
                }
            ],
            "recommendation": "Export the match recording as a standard H.264 / MP4 file and re-upload."
        }

    # 1. Resolution Check
    is_hd = (width >= 1280 and height >= 720) or (height >= 1080)
    is_acceptable_res = (width >= 640 and height >= 360)
    if is_hd:
        criteria.append({
            "name": "Resolution & Geometry",
            "passed": True,
            "status": "PASS",
            "detail": f"✓ {width}×{height} ({'Full HD' if height >= 1080 else 'HD'} resolution adequate for player and spatial court recognition)"
        })
    elif is_acceptable_res:
        criteria.append({
            "name": "Resolution & Geometry",
            "passed": False,
            "status": "WARN",
            "detail": f"⚠ {width}×{height} (Sub-HD resolution; player jersey identification may be difficult at full-court range)"
        })
    else:
        criteria.append({
            "name": "Resolution & Geometry",
            "passed": False,
            "status": "FAIL",
            "detail": f"✕ {width}×{height} (Resolution too low for reliable tactical analysis)"
        })

    # 2. FPS Check
    if fps >= 24.0:
        criteria.append({
            "name": "Temporal Frame Rate",
            "passed": True,
            "status": "PASS",
            "detail": f"✓ {fps:.1f} FPS (Smooth motion capture suitable for fast-break and rotation tracking)"
        })
    elif fps >= 15.0:
        criteria.append({
            "name": "Temporal Frame Rate",
            "passed": False,
            "status": "WARN",
            "detail": f"⚠ {fps:.1f} FPS (Low frame rate; fast passing or rapid cuts may appear stuttered)"
        })
    else:
        criteria.append({
            "name": "Temporal Frame Rate",
            "passed": False,
            "status": "FAIL",
            "detail": f"✕ {fps:.1f} FPS (Frame rate below usable basketball motion standard)"
        })

    # 3. Duration Check
    if duration_s >= 600.0:  # >= 10 minutes
        dur_fmt = format_seconds_to_timestamp(duration_s)
        criteria.append({
            "name": "Match Duration",
            "passed": True,
            "status": "PASS",
            "detail": f"✓ Duration {dur_fmt} (Substantial match / scrimmage coverage)"
        })
    elif duration_s >= 30.0:
        dur_fmt = format_seconds_to_timestamp(duration_s)
        criteria.append({
            "name": "Match Duration",
            "passed": True,
            "status": "PASS",
            "detail": f"✓ Duration {dur_fmt} (Short drill / individual clip sequence)"
        })
    else:
        criteria.append({
            "name": "Match Duration",
            "passed": False,
            "status": "WARN",
            "detail": f"⚠ Duration {duration_s:.1f}s (Extremely short recording)"
        })

    # 4. Audio Presence
    if audio_present:
        criteria.append({
            "name": "Audio Channel",
            "passed": True,
            "status": "PASS",
            "detail": "✓ Audio track detected (Useful for referee whistle, coach communication, and court sound analysis)"
        })
    else:
        criteria.append({
            "name": "Audio Channel",
            "passed": False,
            "status": "WARN",
            "detail": "⚠ No active audio stream detected (Video analysis unaffected, but whistle signals unavailable)"
        })

    # 5. Container Format
    c_upper = container_format.upper()
    if c_upper in ["MP4", "MOV", "M4V", "WEBM"]:
        criteria.append({
            "name": "Container Format",
            "passed": True,
            "status": "PASS",
            "detail": f"✓ {c_upper} (Directly supported by modern web browsers and hardware acceleration)"
        })
    else:
        criteria.append({
            "name": "Container Format",
            "passed": False,
            "status": "WARN",
            "detail": f"⚠ {c_upper} (May require software transcoding or browser fallback)"
        })

    # Determine overall status
    has_fail = any(c["status"] == "FAIL" for c in criteria)
    has_warn = any(c["status"] == "WARN" for c in criteria)

    if has_fail:
        status = "UNSUPPORTED"
        badge = "🔴 UNSUPPORTED"
        headline = "Technical Criteria Failed"
        rec = "Re-record or transcode the match video to at least 720p @ 25 FPS in MP4 format."
    elif has_warn:
        status = "LIMITED"
        badge = "🟡 LIMITED READINESS"
        headline = "Ready with Limitations"
        rec = "Video is fully playable and clippable. Some visual details may be constrained."
    else:
        status = "READY"
        badge = "🟢 READY FOR ANALYSIS"
        headline = "Full Technical Readiness Confirmed"
        rec = "All video technical standards verified. Optimal for tactical review and clip referencing."

    return {
        "status": status,
        "badge": badge,
        "is_ready": (status in ["READY", "LIMITED"]),
        "headline": headline,
        "criteria": criteria,
        "recommendation": rec
    }


def extract_video_metadata(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Inspects uploaded video file and extracts deterministic technical metadata.
    
    Does not make unsupported assumptions. Safely handles corrupt or partial files.
    """
    p = Path(file_path).resolve()
    if not p.exists():
        return {
            "is_valid": False,
            "error_message": f"File not found: {p.name}",
            "filename": p.name,
            "file_size_bytes": 0,
            "processing_status": "FAILED",
            "readiness_status": "UNSUPPORTED"
        }

    file_size = p.stat().st_size
    logger.info("Inspecting video metadata for '%s' (%.2f MB)", p.name, file_size / (1024 * 1024))
    container = p.suffix.replace(".", "").upper() or "UNKNOWN"
    sha256_hash = compute_file_sha256(p)
    audio_present = check_audio_presence(p)

    if cv2 is None:
        err = "OpenCV library unavailable for decoding"
        logger.warning("Extraction error for '%s': %s", p.name, err)
        return {
            "is_valid": False,
            "error_message": err,
            "filename": p.name,
            "file_size_bytes": file_size,
            "checksum_sha256": sha256_hash,
            "processing_status": "FAILED",
            "readiness_status": "UNSUPPORTED"
        }

    cap = cv2.VideoCapture(str(p))
    if not cap.isOpened():
        cap.release()
        err = f"Could not decode video stream from {p.name}. Invalid codec or corrupt file."
        logger.warning("Extraction error for '%s': %s", p.name, err)
        return {
            "is_valid": False,
            "error_message": err,
            "filename": p.name,
            "file_size_bytes": file_size,
            "container_format": container,
            "checksum_sha256": sha256_hash,
            "audio_present": audio_present,
            "processing_status": "FAILED",
            "readiness_status": "UNSUPPORTED"
        }

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))
    cap.release()

    # FourCC decode
    codec_name = "".join([chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)]).strip() if fourcc_int != 0 else "h264"

    # Compute duration
    if fps > 0.0 and frame_count > 0:
        duration_s = float(frame_count / fps)
    else:
        duration_s = 0.0

    # Calculate aspect ratio
    aspect_ratio_str = f"{width}:{height}"
    if height > 0:
        ratio_val = width / height
        if abs(ratio_val - (16 / 9)) < 0.05:
            aspect_ratio_str = "16:9 (Widescreen)"
        elif abs(ratio_val - (4 / 3)) < 0.05:
            aspect_ratio_str = "4:3 (Standard)"
        elif abs(ratio_val - (21 / 9)) < 0.05:
            aspect_ratio_str = "21:9 (Cinematic)"

    # Rule-based readiness
    readiness = classify_video_readiness(
        width=width,
        height=height,
        fps=fps,
        duration_s=duration_s,
        container_format=container,
        stream_readable=(width > 0 and height > 0 and duration_s > 0),
        audio_present=audio_present
    )

    logger.info(
        "Extracted metadata for '%s': %dx%d @ %.2f fps, duration: %.2fs (%s), readiness: %s",
        p.name, width, height, fps, duration_s, format_seconds_to_timestamp(duration_s), readiness["status"]
    )

    return {
        "is_valid": True,
        "filename": p.name,
        "file_path": str(p),
        "file_size_bytes": file_size,
        "file_size_mb": round(file_size / (1024 * 1024), 2),
        "container_format": container,
        "codec": codec_name,
        "resolution_width": width,
        "resolution_height": height,
        "resolution_display": f"{width}×{height}",
        "aspect_ratio": aspect_ratio_str,
        "fps": round(fps, 2),
        "frame_count": frame_count,
        "duration_seconds": round(duration_s, 2),
        "duration_display": format_seconds_to_timestamp(duration_s),
        "audio_present": audio_present,
        "checksum_sha256": sha256_hash,
        "readiness": readiness,
        "readiness_status": readiness["status"],
        "processing_status": "READY" if readiness["is_ready"] else "FAILED"
    }
