"""Event payload dataclasses."""

from dataclasses import dataclass, field


@dataclass
class IngestRequestedPayload:
    """Payload for architecture.ingest.requested."""

    file_path: str | None = None
    content: str | None = None
    correlation_id: str = ""


@dataclass
class ProcessingCompletedPayload:
    """Payload for architecture.processing.completed."""

    correlation_id: str
    output_path: str
    summary: dict = field(default_factory=dict)


@dataclass
class ProcessingFailedPayload:
    """Payload for architecture.processing.failed."""

    correlation_id: str
    stage: str
    error: str
    partial_uploads: list[str] | None = None  # For artifact_upload failures
