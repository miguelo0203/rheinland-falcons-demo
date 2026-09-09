# Video Evidence & Clip Reference Layer — Technical Specification (v1)

## 1. Architectural Philosophy: "Video is Evidence"

In the Rheinland Falcons Basketball Intelligence Platform, video recordings are not isolated files or simple media players. Instead, match footage is treated as a **first-class source of tactical and developmental evidence** permanently interconnected with the rest of the operating system:

$$\text{Match} \longrightarrow \text{Video} \longrightarrow \text{Video Evidence} \longrightarrow \begin{cases} \text{Athlete Dossiers (e.g. Player \#7)} \\ \text{Player Development Objectives} \\ \text{Coach Tactical Notes} \\ \text{Match Reports \& Deep Dive} \\ \text{Team Tactical Analysis} \end{cases}$$

Every video clip is an atomic, immutable, temporally precise entity referenced by a unique ID (`evidence_id`). No module duplicates video clip metadata; all features resolve the canonical entity by ID.

---

## 2. Canonical Data Models

### A. Video Entity (`python.models.canonical.Video`)
```python
class Video(BaseCanonicalModel):
    video_id: str
    game_id: str
    file_path: str
    filename: Optional[str] = None
    duration_seconds: Optional[float] = None
    container_format: Optional[str] = None
    codec: Optional[str] = None
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None
    fps: Optional[float] = None
    file_size_bytes: Optional[int] = None
    checksum_sha256: str
    camera_angle: Optional[str] = None
    analysis_focus: Optional[List[str]] = Field(default_factory=list)
    notes: Optional[str] = None
    processing_status: str = "READY"    # READY, LIMITED, FAILED
    readiness_status: str = "READY"     # READY, LIMITED, UNSUPPORTED
    audio_present: bool = True
    created_by: str = "Staff"
    ingestion_timestamp: datetime
```

### B. VideoEvidence Entity (`python.models.canonical.VideoEvidence`)
```python
class VideoEvidence(BaseCanonicalModel):
    evidence_id: str                    # Surrogate ID: EVD_...
    video_id: str                       # References video(video_id)
    game_id: str                        # References game(game_id)
    start_time_s: float                 # Sub-second boundary e.g. 871.2 (14:31.2)
    end_time_s: float                   # Sub-second boundary e.g. 888.7 (14:48.7)
    title: str                          # Clip Headline
    category: str                       # Defense, Offense, Transition, Development
    subcategory: Optional[str] = None   # e.g. Weak-side rotation, P&R coverage
    tags: List[str]                     # Searchable tactical tags
    description: Optional[str] = None   # Coaching narrative
    player_ids: List[str]               # Canonical IDs: ['PLY_DEMO_102'] (#7 Jonas Keller)
    team_id: Optional[str] = None       # e.g. TEM_DEMO_U16
    source: str = "Coach"               # Coach, AI, AI + Coach Review
    confidence: Optional[float] = None  # e.g. 0.82 for future AI tagging
    review_status: str = "CONFIRMED"    # CONFIRMED, PENDING_REVIEW, REJECTED
    created_by: str = "Coach"
    created_at: datetime
```

### Validation Invariants:
$$0 \le \text{start\_time\_s} < \text{end\_time\_s} \le \text{video.duration\_seconds}$$

---

## 3. Technical Metadata Extraction & Deterministic Readiness

When video recordings are ingested, `python.analytics.video_metadata.extract_video_metadata()` deterministically inspects the media stream via OpenCV and Mutagen:
1. **Container & Codec:** Inspects header atoms and FourCC streams (`MP4`, `MOV`, `MKV`, `WEBM`, `AVI`).
2. **Resolution & Geometry:** Width, height, aspect ratio (`16:9`, `4:3`, `21:9`).
3. **Temporal Sampling:** Frame count, verified frames per second (FPS), and duration.
4. **Audio Verification:** Verifies audio presence without fabricated claims.
5. **SHA-256 Provenance:** Cryptographic hash computed over all bytes for auditability.

### Video Analysis Readiness Rules:
- **`🟢 READY FOR ANALYSIS`**: Resolution $\ge 720p$, FPS $\ge 24$, duration $\ge 30$s, audio track present, video stream decodable.
- **`🟡 LIMITED READINESS`**: Sub-HD resolution ($< 720p$), low frame rate ($< 20$ FPS), or missing audio. The video is fully playable and clippable, but visual resolution may constrain jersey identification.
- **`🔴 UNSUPPORTED`**: Corrupt stream, zero-byte file, unreadable frames, or duration $\le 0$.

---

## 4. Strict Official vs Practice Population Isolation

The platform enforces strict mathematical separation between official competition fixtures and practice/scrimmage games:
- **`OFFICIAL` Fixtures:** Inform Dean Oliver Four Factors, player season statistics, percentile distributions, and qualified league benchmarks.
- **`PRACTICE` / `SCRIMMAGE` / `FRIENDLY` Fixtures:** Available for video review, tactical experiments, and player development tracking, but **strictly filtered out** from official competitive analytics (`filter_by_population(df, "OFFICIAL_ONLY")`).

---

## 5. Cross-Platform Reference Architecture

1. **Player Profile (Hub 1):**
   - Displays **"📹 Verified Video Evidence & Film Anchors"** grouped into Development Opportunities (e.g. Weak-side defense, turnovers) and Positive Examples (e.g. Transition decision-making).
   - Clicking `▶ Play Clip` instantly switches to Hub 7 with the player positioned at the exact second.
2. **Player Development Objectives (Hub 1 & Hub 6):**
   - Coaches define development milestones and attach verified video evidence clips by ID.
3. **Coach Notes (Hub 1 & Hub 3):**
   - Observations (e.g. *"Need better communication when defending P&R"*) attach specific evidence clips.
4. **Game Lab & Match Deep Dive (Hub 3):**
   - Modality Availability Matrix dynamically exposes film availability (`✅ YES — X clips`).
   - Match Video Evidence Library embeds all tagged clips with direct links.

---

## 6. Future AI & Computer Vision Roadmap

The data layer is engineered for seamless future AI expansion without database re-architecting:
$$\text{VIDEO} \longrightarrow \text{CV Tracking / Detection} \longrightarrow \text{VideoEvidence (source='AI', confidence=0.82, status='PENDING\_REVIEW')} \longrightarrow \text{Coach Review}$$
Coaches can confirm, edit, or reclassify AI-proposed evidence directly in the platform.
