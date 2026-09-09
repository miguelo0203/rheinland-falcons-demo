"""Pydantic v2 Domain Models for the Canonical Basketball Schema."""

from datetime import date, datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from python.models.enums import (
    ObservationStatus,
    EventType,
    ShotType,
    ShotZone,
    PeriodType,
    ValidationSeverity,
    ValidationStatus,
    CompletenessTier,
    QualityTier,
    SourceType,
    ConfidenceStatus,
    ReconstructionMethod,
)


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BaseCanonicalModel(BaseModel):
    """Base model with strict typing and serialization configuration."""
    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="forbid",
        arbitrary_types_allowed=True,
    )


class Competition(BaseCanonicalModel):
    competition_id: str = Field(..., description="Surrogate ID: CMP_...")
    name: str
    gender: Optional[str] = None
    age_category: Optional[str] = None
    country: Optional[str] = None
    governing_body: Optional[str] = None
    created_at: datetime = Field(default_factory=get_utc_now)


class Season(BaseCanonicalModel):
    season_id: str = Field(..., description="Surrogate ID: SEA_...")
    competition_id: str
    name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class Team(BaseCanonicalModel):
    team_id: str = Field(..., description="Surrogate ID: TEM_...")
    canonical_name: str
    short_name: Optional[str] = None
    club_name: Optional[str] = None
    age_category: Optional[str] = None
    created_at: datetime = Field(default_factory=get_utc_now)


class Player(BaseCanonicalModel):
    player_id: str = Field(..., description="Surrogate ID: PLY_...")
    canonical_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[date] = None
    height_cm: Optional[float] = None
    listed_position: Optional[str] = None  # Never mandatory; position is independent
    nationality: Optional[str] = None
    created_at: datetime = Field(default_factory=get_utc_now)


class PlayerTeam(BaseCanonicalModel):
    player_team_id: str
    player_id: str
    team_id: str
    season_id: str
    jersey_number: Optional[str] = None
    is_active: bool = True


class Game(BaseCanonicalModel):
    game_id: str = Field(..., description="Surrogate ID: GAM_...")
    season_id: str
    competition_id: str
    game_date: date
    game_time: Optional[str] = None
    round_number: Optional[int] = None
    home_team_id: str
    away_team_id: str
    venue: Optional[str] = None
    periods_played: int = 4
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    game_status: str = "FINAL"
    game_type: str = "OFFICIAL"


class GameSources(BaseCanonicalModel):
    game_id: str
    boxscore_available: bool = False
    pbp_available: bool = False
    video_available: bool = False
    shot_chart_available: bool = False
    boxscore_file_path: Optional[str] = None
    pbp_file_path: Optional[str] = None
    video_file_path: Optional[str] = None
    validation_status: ValidationStatus = ValidationStatus.UNVALIDATED
    completeness_score: CompletenessTier = CompletenessTier.MINIMAL
    overall_quality: QualityTier = QualityTier.LOW
    updated_at: datetime = Field(default_factory=get_utc_now)


class SourceProvenance(BaseCanonicalModel):
    provenance_id: str = Field(..., description="Surrogate ID: PRV_...")
    source_type: SourceType
    source_provider: str
    source_file_path: str
    source_file_hash: str
    parser_version: str
    pipeline_version: str
    ingestion_timestamp: datetime = Field(default_factory=get_utc_now)


class GameRoster(BaseCanonicalModel):
    game_roster_id: str
    game_id: str
    team_id: str
    player_id: str
    jersey_number: Optional[str] = None
    is_starter: Optional[bool] = None
    is_captain: Optional[bool] = None
    is_active: bool = True
    provenance_id: str


class BoxscoreTeam(BaseCanonicalModel):
    boxscore_team_id: str
    game_id: str
    team_id: str
    is_home: bool
    points: int
    fgm: Optional[int] = None
    fga: Optional[int] = None
    fg2m: Optional[int] = None
    fg2a: Optional[int] = None
    fg3m: Optional[int] = None
    fg3a: Optional[int] = None
    ftm: Optional[int] = None
    fta: Optional[int] = None
    orb: Optional[int] = None
    drb: Optional[int] = None
    trb: Optional[int] = None
    ast: Optional[int] = None
    stl: Optional[int] = None
    blk: Optional[int] = None
    tov: Optional[int] = None
    pf: Optional[int] = None
    team_rebounds: Optional[int] = None
    team_turnovers: Optional[int] = None
    provenance_id: str


class BoxscorePlayer(BaseCanonicalModel):
    boxscore_player_id: str
    game_id: str
    team_id: str
    player_id: str
    jersey_number: Optional[str] = None
    seconds_played: Optional[int] = None
    points: int
    fgm: Optional[int] = None
    fga: Optional[int] = None
    fg2m: Optional[int] = None
    fg2a: Optional[int] = None
    fg3m: Optional[int] = None
    fg3a: Optional[int] = None
    ftm: Optional[int] = None
    fta: Optional[int] = None
    orb: Optional[int] = None
    drb: Optional[int] = None
    trb: Optional[int] = None
    ast: Optional[int] = None
    stl: Optional[int] = None
    blk: Optional[int] = None
    tov: Optional[int] = None
    pf: Optional[int] = None
    plus_minus: Optional[int] = None
    is_dnp: bool = False
    dnp_reason: Optional[str] = None
    observation_status: ObservationStatus = ObservationStatus.OBSERVED
    provenance_id: str


class PBPEvent(BaseCanonicalModel):
    event_id: str
    game_id: str
    period: int
    period_type: PeriodType = PeriodType.REGULAR
    clock_display: str
    game_seconds_remaining: float
    period_seconds_remaining: float
    event_index: int
    event_type: EventType
    event_subtype: Optional[str] = None
    team_id: Optional[str] = None
    player_id: Optional[str] = None
    secondary_player_id: Optional[str] = None
    home_score: int
    away_score: int
    score_margin: int
    points_scored: int = 0
    description: Optional[str] = None
    possession_id: Optional[str] = None
    provenance_id: str


class Shot(BaseCanonicalModel):
    shot_id: str
    event_id: Optional[str] = None
    game_id: str
    team_id: str
    player_id: str
    period: int
    game_seconds_remaining: Optional[float] = None
    shot_type: ShotType
    shot_subtype: Optional[str] = None
    is_made: bool
    points: int
    x_coord: Optional[float] = None
    y_coord: Optional[float] = None
    shot_distance_m: Optional[float] = None
    shot_zone: Optional[ShotZone] = None
    shot_location_status: ObservationStatus = ObservationStatus.NOT_AVAILABLE
    assisted_by_player_id: Optional[str] = None
    provenance_id: str


class LineupStint(BaseCanonicalModel):
    stint_id: str
    game_id: str
    team_id: str
    period: int
    start_game_seconds: float
    end_game_seconds: float
    duration_seconds: float
    player_ids: str  # Comma-separated sorted canonical IDs
    is_home: bool
    points_for: int
    points_against: int
    reconstruction_method: ReconstructionMethod = ReconstructionMethod.EXACT_SUB_TRACKING
    confidence_status: ConfidenceStatus = ConfidenceStatus.EXACT
    provenance_id: str


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
    processing_status: str = "READY"
    readiness_status: str = "READY"
    audio_present: bool = True
    created_by: str = "Staff"
    ingestion_timestamp: datetime = Field(default_factory=get_utc_now)


class VideoEvidence(BaseCanonicalModel):
    evidence_id: str = Field(..., description="Surrogate ID: EVD_...")
    video_id: str
    game_id: str
    start_time_s: float
    end_time_s: float
    title: str
    category: str
    subcategory: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    player_ids: List[str] = Field(default_factory=list)
    team_id: Optional[str] = None
    source: str = "Coach"
    confidence: Optional[float] = None
    review_status: str = "CONFIRMED"
    created_by: str = "Coach"
    created_at: datetime = Field(default_factory=get_utc_now)


class CoachNote(BaseCanonicalModel):
    note_id: str = Field(..., description="Surrogate ID: NOT_...")
    author: str = "Coach"
    player_id: Optional[str] = None
    team_id: Optional[str] = None
    game_id: Optional[str] = None
    title: str
    content: str
    category: Optional[str] = None
    evidence_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)


class PlayerDevelopmentObjective(BaseCanonicalModel):
    objective_id: str = Field(..., description="Surrogate ID: OBJ_...")
    player_id: str
    title: str
    category: str
    target_description: str
    status: str = "IN_PROGRESS"
    evidence_ids: List[str] = Field(default_factory=list)
    created_by: str = "Coach"
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)


class VideoEventSync(BaseCanonicalModel):
    sync_id: str
    event_id: Optional[str] = None
    game_id: str
    video_id: str
    video_start_time_s: float
    video_end_time_s: float
    confidence_level: str = "HIGH"
    sync_method: str = "MANUAL"
    verified_by: Optional[str] = None


class EntityAlias(BaseCanonicalModel):
    alias_id: str
    entity_type: str
    canonical_id: str
    source_provider: str
    source_id: Optional[str] = None
    source_name_raw: str
    normalized_name: str
    jersey_number: Optional[str] = None
    match_confidence: float = 1.0
    requires_review: bool = False


class SourceConflictLog(BaseCanonicalModel):
    conflict_id: str
    game_id: str
    entity_table: str
    entity_id: str
    field_name: str
    source_a_type: str
    source_a_value: str
    source_b_type: str
    source_b_value: str
    resolution_policy: str
    resolved_value: str
    logged_at: datetime = Field(default_factory=get_utc_now)


class ValidationLog(BaseCanonicalModel):
    validation_id: str
    game_id: str
    rule_id: str
    rule_category: str
    severity: ValidationSeverity
    status: str
    message: str
    details_json: Optional[str] = None
    timestamp: datetime = Field(default_factory=get_utc_now)
