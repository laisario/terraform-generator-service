"""Configuration using Pydantic Settings."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_prefix="TFGEN_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # From ENVIRONMENT (no TFGEN_ prefix)
    environment: str = Field(default="dev", validation_alias="ENVIRONMENT")

    output_dir: Path = Path("output")
    max_file_size_bytes: int = 1_048_576  # 1MB
    schema_path: Path = Path("schemas/architecture_v1.json")
    input_schema_path: Path = Path("schemas/input_v1.json")
    templates_dir: Path = Path("templates/terraform/aws")

    # Storage (production only)
    storage_bucket: str = "vibe-cloud"
    storage_prefix: str = "output"  # Must match output_dir name for consistent S3 keys
    s3_api_url: str | None = Field(default=None, validation_alias="S3_API")
    aws_access_key_id: str | None = Field(default=None, validation_alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str | None = Field(default=None, validation_alias="AWS_SECRET_ACCESS_KEY")
