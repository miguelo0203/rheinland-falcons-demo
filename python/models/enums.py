"""Standardized Enumerations for the Canonical Basketball Data Model."""

from enum import Enum


class ObservationStatus(str, Enum):
    """Observation and missingness statuses according to epistemic standards."""
    OBSERVED = "OBSERVED"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_OBSERVED = "NOT_OBSERVED"
    ESTIMATED = "ESTIMATED"


class EventType(str, Enum):
    """Canonical basketball event types."""
    SHOT = "SHOT"
    FREE_THROW = "FREE_THROW"
    REBOUND = "REBOUND"
    TURNOVER = "TURNOVER"
    FOUL = "FOUL"
    VIOLATION = "VIOLATION"
    SUB = "SUB"
    TIMEOUT = "TIMEOUT"
    JUMP_BALL = "JUMP_BALL"
    PERIOD_START = "PERIOD_START"
    PERIOD_END = "PERIOD_END"
    GAME_END = "GAME_END"


class ShotType(str, Enum):
    """Point value category of field goal."""
    TWO_POINT = "2PT"
    THREE_POINT = "3PT"


class ShotZone(str, Enum):
    """Qualitative court zones for shot attempts."""
    RESTRICTED_AREA = "RESTRICTED_AREA"
    PAINT_NON_RA = "PAINT_NON_RA"
    MID_RANGE = "MID_RANGE"
    CORNER_3 = "CORNER_3"
    ABOVE_BREAK_3 = "ABOVE_BREAK_3"


class PeriodType(str, Enum):
    """Game period class."""
    REGULAR = "REGULAR"
    OVERTIME = "OVERTIME"


class ValidationSeverity(str, Enum):
    """Severity tier for validation rules."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ValidationStatus(str, Enum):
    """Health status resulting from validation engine."""
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    FAIL_WITH_ERRORS = "FAIL_WITH_ERRORS"
    UNVALIDATED = "UNVALIDATED"


class CompletenessTier(str, Enum):
    """Completeness score tier."""
    COMPLETE = "COMPLETE"
    HIGH = "HIGH"
    PARTIAL = "PARTIAL"
    MINIMAL = "MINIMAL"


class QualityTier(str, Enum):
    """Composite data quality tier."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    COMPROMISED = "COMPROMISED"


class SourceType(str, Enum):
    """External data modality type."""
    BOXSCORE = "BOXSCORE"
    PBP = "PBP"
    VIDEO = "VIDEO"
    ROSTER = "ROSTER"
    COMBINED = "COMBINED"


class SourceProvider(str, Enum):
    """Known source data providers and formats."""
    FIBA_LIVESTATS = "FIBA_LIVESTATS"
    NBN23 = "NBN23"
    DBB = "DBB"
    FEB = "FEB"
    GENERIC_CSV = "GENERIC_CSV"
    VIDEO_METADATA = "VIDEO_METADATA"


class ConfidenceStatus(str, Enum):
    """Derivation certainty level."""
    EXACT = "EXACT"
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
    ESTIMATED = "ESTIMATED"
    AMBIGUOUS = "AMBIGUOUS"


class ReconstructionMethod(str, Enum):
    """Algorithm used for possession / lineup reconstruction."""
    EXACT_SUB_TRACKING = "EXACT_SUB_TRACKING"
    INFERRED_STARTERS = "INFERRED_STARTERS"
    MANUAL_VIDEO = "MANUAL_VIDEO"
    APPROXIMATE_PBP = "APPROXIMATE_PBP"
