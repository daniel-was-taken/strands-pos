"""Centralized configuration with startup validation.

All environment variable access should go through this module.
Import `settings` to access configuration values.
"""

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    # Database (PostgreSQL for request state)
    database_url: str

    # Neon MCP connection
    neon_api_key: str
    neon_project_id: str
    neon_database: str
    neon_branch_id: str
    neon_mcp_url: str

    # Gemini model
    gemini_model_id: str
    google_api_key: str | None
    google_cloud_project: str | None
    google_cloud_location: str

    # Application
    log_level: str


def _require(key: str, missing: list[str]) -> str:
    """Get required environment variable or track as missing."""
    val = os.environ.get(key)
    if not val:
        missing.append(key)
    return val or ""


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    """Load and validate settings from environment variables.

    Raises:
        EnvironmentError: If required variables are missing.
    """
    missing: list[str] = []

    settings = Settings(
        # Database
        database_url=_require("DATABASE_URL", missing),
        # Neon MCP
        neon_api_key=_require("NEON_API_KEY", missing),
        neon_project_id=_require("NEON_PROJECT_ID", missing),
        neon_database=_require("NEON_DATABASE", missing),
        neon_branch_id=_require("NEON_BRANCH_ID", missing),
        neon_mcp_url=os.environ.get("NEON_MCP_URL", "https://mcp.neon.tech/mcp"),
        # Gemini model
        gemini_model_id=os.environ.get("GEMINI_MODEL_ID", "gemini-3-flash"),
        google_api_key=os.environ.get("GOOGLE_API_KEY"),
        google_cloud_project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
        google_cloud_location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
        # Application
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
    )

    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    return settings


# Convenience function for lazy loading - doesn't fail at import time
def get_settings() -> Settings:
    """Get the settings singleton. Call this instead of load_settings() for lazy loading."""
    return load_settings()
