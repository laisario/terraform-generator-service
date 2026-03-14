"""Domain exceptions."""


class TerraformGeneratorError(Exception):
    """Base exception for Terraform Generator Service."""


class IngestionError(TerraformGeneratorError):
    """Error during ingestion (file not found, encoding, JSON parse, etc.)."""


class InputValidationError(TerraformGeneratorError):
    """Error during JSON input validation (schema, structure, required fields)."""


class NormalizationError(TerraformGeneratorError):
    """Error during normalization (e.g., circular dependency)."""


class ValidationError(TerraformGeneratorError):
    """Error during validation (schema or custom rules)."""


class GenerationError(TerraformGeneratorError):
    """Error during Terraform file generation."""


class UploadError(TerraformGeneratorError):
    """Error during artifact upload to object storage."""
