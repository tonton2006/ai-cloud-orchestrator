"""
Configuration Management

Loads configuration from environment variables using Pydantic Settings.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be configured via environment variables or .env file.
    """

    # GCP Configuration
    gcp_project_id: str = Field(
        ...,
        description="Google Cloud Project ID",
        validation_alias="GCP_PROJECT_ID"
    )

    gcp_region: str = Field(
        default="us-central1",
        description="Default GCP region for resources",
        validation_alias="GCP_REGION"
    )

    default_zone: str = Field(
        default="us-central1-a",
        description="Default GCP zone for Compute Engine resources",
        validation_alias="DEFAULT_ZONE"
    )

    # Application Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        validation_alias="LOG_LEVEL"
    )

    # Model configuration for loading from .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
