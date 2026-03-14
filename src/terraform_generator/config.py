"""Configuration using Pydantic Settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_prefix="TFGEN_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    output_dir: Path = Path("output")
    max_file_size_bytes: int = 1_048_576  # 1MB
    schema_path: Path = Path("schemas/architecture_v1.json")
    templates_dir: Path = Path("templates/terraform/aws")
