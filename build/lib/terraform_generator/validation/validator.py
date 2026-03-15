"""JSON Schema and custom rule validation."""

import json
from dataclasses import dataclass, field
from pathlib import Path

import jsonschema
from jsonschema import Draft202012Validator

from terraform_generator.domain.models import Architecture

from terraform_generator.validation.rules import (
    ValidationIssue,
    check_empty_resources,
    check_required_attributes,
)


@dataclass
class ValidationResult:
    """Result of validation."""

    valid: bool
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)


class Validator:
    """Validate Architecture against JSON Schema and custom rules."""

    def __init__(self, schema_path: Path | None = None) -> None:
        self.schema_path = schema_path or Path("schemas/architecture_v1.json")
        self._schema = self._load_schema()

    def _load_schema(self) -> dict:
        """Load JSON Schema from file."""
        # Try project root (4 levels up from validation/validator.py)
        base = Path(__file__).resolve().parent.parent.parent.parent
        path = base / self.schema_path
        if not path.exists():
            path = Path(self.schema_path)
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def validate(self, architecture: Architecture) -> ValidationResult:
        """Validate architecture. Returns ValidationResult."""
        errors: list[ValidationIssue] = []
        warnings: list[ValidationIssue] = []

        # Convert to dict for schema validation
        data = architecture.model_dump(mode="json")
        # Ensure parsed_at is ISO string
        if architecture.metadata:
            data.setdefault("metadata", {})
            data["metadata"]["parsed_at"] = architecture.metadata.parsed_at.isoformat() + "Z"

        # JSON Schema validation
        try:
            Draft202012Validator(self._schema).validate(data)
        except jsonschema.ValidationError as e:
            errors.append(
                ValidationIssue(
                    code="invalid_schema",
                    message=str(e.message),
                    path=".".join(str(p) for p in e.absolute_path) if e.absolute_path else None,
                )
            )
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        # Custom rules
        warnings.extend(check_empty_resources(architecture.resources))

        for resource in architecture.resources:
            issues = check_required_attributes(resource.type, resource.attributes)
            errors.extend(issues)

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
