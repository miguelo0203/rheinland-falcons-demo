"""Configuration loader and directory manager for the Sandbox Data Foundation."""

from pathlib import Path
from typing import Any, Dict, Optional
import yaml

import os

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT_DIR / "config" / "settings.yaml"


def _load_env_file() -> Dict[str, str]:
    """Parse local .env file securely if present."""
    env_file = ROOT_DIR / ".env"
    env_vars: Dict[str, str] = {}
    if env_file.exists():
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip()
        except Exception:
            pass
    return env_vars


ENV_VARS = _load_env_file()


def get_api_key(league: str) -> Optional[str]:
    """Securely retrieves federation API key for JBBL or NBBL without leaking credentials."""
    league_upper = league.upper()
    # 1. System environment variable
    key = os.environ.get(f"SCB_{league_upper}_KEY") or os.environ.get(f"{league_upper}_KEY")
    if key:
        return key
    # 2. Local .env file
    key = ENV_VARS.get(f"SCB_{league_upper}_KEY") or ENV_VARS.get(f"{league_upper}_KEY")
    if key:
        return key
    # 3. Streamlit secrets
    try:
        import streamlit as st
        secret_key = f"scb_{league.lower()}_key"
        if hasattr(st, "secrets") and secret_key in st.secrets:
            return str(st.secrets[secret_key])
    except Exception:
        pass
    return None


def load_config() -> Dict[str, Any]:
    """Load settings from YAML configuration file."""
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


CONFIG = load_config()



class Settings:
    ROOT_DIR: Path = ROOT_DIR
    CONFIG: Dict[str, Any] = CONFIG
    PIPELINE_VERSION: str = CONFIG.get("project", {}).get("pipeline_version", "1.0.0")
    SCHEMA_VERSION: str = CONFIG.get("project", {}).get("schema_version", "1.0.0")

    # Directory Paths
    RAW_DIR: Path = ROOT_DIR / CONFIG.get("paths", {}).get("raw_dir", "data/raw")
    STAGING_DIR: Path = ROOT_DIR / CONFIG.get("paths", {}).get("staging_dir", "data/staging")
    NORMALIZED_DIR: Path = ROOT_DIR / CONFIG.get("paths", {}).get("normalized_dir", "data/normalized")
    VALIDATED_DIR: Path = ROOT_DIR / CONFIG.get("paths", {}).get("validated_dir", "data/validated")
    DERIVED_DIR: Path = ROOT_DIR / CONFIG.get("paths", {}).get("derived_dir", "data/derived")
    ANALYTICS_DIR: Path = ROOT_DIR / CONFIG.get("paths", {}).get("analytics_dir", "data/analytics")
    DATABASE_PATH: Path = ROOT_DIR / CONFIG.get("paths", {}).get("database_path", "database/jbbl_sandbox.duckdb")
    LOGS_DIR: Path = ROOT_DIR / CONFIG.get("paths", {}).get("logs_dir", "logs")
    REPORTS_DIR: Path = ROOT_DIR / CONFIG.get("paths", {}).get("reports_dir", "reports")

    # Tolerances
    RECONCILIATION_TOLERANCES: Dict[str, Any] = CONFIG.get("reconciliation_tolerances", {})
    ENTITY_RESOLUTION: Dict[str, Any] = CONFIG.get("entity_resolution", {})
    SOURCE_PRECEDENCE: Dict[str, Any] = CONFIG.get("source_precedence", {})

    @classmethod
    def ensure_directories(cls):
        """Ensure all project directories exist."""
        for path in [
            cls.RAW_DIR / "boxscore",
            cls.RAW_DIR / "pbp",
            cls.RAW_DIR / "video",
            cls.STAGING_DIR,
            cls.NORMALIZED_DIR,
            cls.VALIDATED_DIR,
            cls.DERIVED_DIR,
            cls.ANALYTICS_DIR,
            cls.DATABASE_PATH.parent,
            cls.LOGS_DIR,
            cls.REPORTS_DIR,
        ]:
            path.mkdir(parents=True, exist_ok=True)
