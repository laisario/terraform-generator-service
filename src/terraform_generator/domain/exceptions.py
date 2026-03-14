"""Domain exceptions."""


class TerraformGeneratorError(Exception):
    """Base exception for Terraform Generator Service."""


class IngestionError(TerraformGeneratorError):
    """Error during Markdown ingestion (file not found, encoding, etc.)."""


class ParsingError(TerraformGeneratorError):
    """Error during Markdown parsing."""


class ExtractionError(TerraformGeneratorError):
    """Error during infrastructure requirement extraction."""


class NormalizationError(TerraformGeneratorError):
    """Error during normalization (e.g., circular dependency)."""


class ValidationError(TerraformGeneratorError):
    """Error during validation (schema or custom rules)."""


class GenerationError(TerraformGeneratorError):
    """Error during Terraform file generation."""
