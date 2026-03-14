"""Validate JSON input against input_v1 schema."""

import json
from pathlib import Path

import jsonschema

from terraform_generator.config import Settings
from terraform_generator.domain.exceptions import InputValidationError


class InputValidator:
    """Validate incoming JSON against schemas/input_v1.json."""

    def __init__(self, schema_path: Path | None = None, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.schema_path = schema_path or self.settings.input_schema_path

    def validate(self, data: dict) -> dict:
        """
        Validate data against input schema.
        Returns validated data (unchanged) on success.
        Raises InputValidationError on failure.
        """
        base = Path(__file__).resolve().parent.parent.parent.parent
        path = base / self.schema_path
        if not path.exists():
            path = Path(self.schema_path)
        if not path.exists():
            raise InputValidationError(f"Input schema not found: {path}")

        schema = json.loads(path.read_text(encoding="utf-8"))

        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as e:
            path_str = ".".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
            raise InputValidationError(
                f"Input validation failed at '{path_str}': {e.message}"
            ) from e

        return data
