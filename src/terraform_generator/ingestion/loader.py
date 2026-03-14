"""Load Markdown from file path or content."""

from pathlib import Path

from terraform_generator.config import Settings
from terraform_generator.domain.exceptions import IngestionError


class Loader:
    """Load Markdown content from file path or raw string."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()

    def load_from_path(self, file_path: str | Path) -> str:
        """Load Markdown from a file path."""
        path = Path(file_path)
        if not path.exists():
            raise IngestionError(f"File not found: {path}")
        if not path.is_file():
            raise IngestionError(f"Not a file: {path}")

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise IngestionError(f"Encoding error reading {path}: {e}") from e

        if len(content.encode("utf-8")) > self.settings.max_file_size_bytes:
            raise IngestionError(
                f"File exceeds size limit ({self.settings.max_file_size_bytes} bytes): {path}"
            )

        return content

    def load_from_content(self, content: str) -> str:
        """Load Markdown from raw string (passthrough)."""
        return content
