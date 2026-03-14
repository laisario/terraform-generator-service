"""Load JSON input from file path or content."""

import json
from pathlib import Path

from terraform_generator.config import Settings
from terraform_generator.domain.exceptions import IngestionError


class Loader:
    """Load JSON input from file path or raw string."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()

    def load_from_path(self, file_path: str | Path) -> dict:
        """Load and parse JSON from a file path."""
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

        return self._parse_json(content, str(path))

    def load_from_content(self, content: str) -> dict:
        """Load and parse JSON from raw string."""
        return self._parse_json(content, source="<content>")

    def _parse_json(self, content: str, source: str) -> dict:
        """Parse JSON string to dict. Raises IngestionError on parse failure."""
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise IngestionError(f"Invalid JSON in {source}: {e}") from e

        if not isinstance(data, dict):
            raise IngestionError(f"Expected JSON object, got {type(data).__name__}")

        return data
