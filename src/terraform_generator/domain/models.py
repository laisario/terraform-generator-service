"""Domain models for the Terraform Generator Service."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ArchitectureMetadata(BaseModel):
    """Document-level metadata."""

    source_file: str | None = None
    parsed_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0"


class InfrastructureResource(BaseModel):
    """A single infrastructure component (e.g., S3 bucket, EC2 instance)."""

    type: str  # e.g., "aws_s3_bucket", "aws_instance"
    logical_name: str  # Terraform resource name (e.g., "main_bucket")
    attributes: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)


class Architecture(BaseModel):
    """Root container for a single architecture definition."""

    id: str  # correlation_id
    name: str = "architecture"
    provider: str = "aws"
    resources: list[InfrastructureResource] = Field(default_factory=list)
    metadata: ArchitectureMetadata = Field(default_factory=ArchitectureMetadata)
