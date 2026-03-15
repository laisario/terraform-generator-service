"""Unit tests for input validation."""

from pathlib import Path

import pytest

from terraform_generator.config import Settings
from terraform_generator.domain.exceptions import InputValidationError
from terraform_generator.input.validator import InputValidator


def test_validate_valid_array_with_one_item():
    """Valid array with one item and output passes."""
    data = [{"output": {"analise_entrada": "test summary"}}]
    validator = InputValidator(settings=Settings())
    result = validator.validate(data)
    assert result == data


def test_validate_valid_array_with_vibes():
    """Valid array with vibes and recursos passes."""
    data = [
        {
            "output": {
                "analise_entrada": "test",
                "vibe_economica": {
                    "descricao": "economy",
                    "recursos": [{"servico": "aws_s3_bucket", "config": {"bucket": "my-bucket"}}],
                },
            }
        }
    ]
    validator = InputValidator(settings=Settings())
    result = validator.validate(data)
    assert len(result) == 1
    assert result[0]["output"]["analise_entrada"] == "test"
    assert len(result[0]["output"]["vibe_economica"]["recursos"]) == 1


def test_validate_rejects_empty_array():
    """Reject empty array."""
    validator = InputValidator(settings=Settings())
    with pytest.raises(InputValidationError):
        validator.validate([])


def test_validate_rejects_item_without_output():
    """Reject item missing output field."""
    data = [{"other_field": "no output"}]
    validator = InputValidator(settings=Settings())
    with pytest.raises(InputValidationError):
        validator.validate(data)


def test_validate_rejects_output_not_object():
    """Reject item where output is not an object."""
    data = [{"output": "string not object"}]
    validator = InputValidator(settings=Settings())
    with pytest.raises(InputValidationError):
        validator.validate(data)


def test_validate_rejects_missing_analise_entrada_in_output():
    """Reject when output lacks required analise_entrada."""
    data = [{"output": {"vibe_economica": {"recursos": []}}}]
    validator = InputValidator(settings=Settings())
    with pytest.raises(InputValidationError):
        validator.validate(data)
