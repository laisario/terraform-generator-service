"""Unit tests for input validation."""

from pathlib import Path

import pytest

from terraform_generator.config import Settings
from terraform_generator.domain.exceptions import InputValidationError
from terraform_generator.input.validator import InputValidator


def test_validate_valid_input():
    """Valid JSON with analise_entrada passes."""
    data = {"analise_entrada": "test summary"}
    validator = InputValidator(settings=Settings())
    result = validator.validate(data)
    assert result == data


def test_validate_valid_input_with_vibes():
    """Valid JSON with vibes and recursos passes."""
    data = {
        "analise_entrada": "test",
        "vibe_economica": {
            "descricao": "economy",
            "recursos": [{"servico": "aws_s3_bucket", "config": {"bucket": "my-bucket"}}],
        },
    }
    validator = InputValidator(settings=Settings())
    result = validator.validate(data)
    assert result["analise_entrada"] == "test"
    assert len(result["vibe_economica"]["recursos"]) == 1


def test_validate_rejects_missing_analise_entrada():
    """Reject JSON missing required analise_entrada."""
    data = {"vibe_economica": {"recursos": []}}
    validator = InputValidator(settings=Settings())
    with pytest.raises(InputValidationError, match="analise_entrada|validation failed"):
        validator.validate(data)


def test_validate_rejects_empty_object():
    """Reject empty object."""
    validator = InputValidator(settings=Settings())
    with pytest.raises(InputValidationError):
        validator.validate({})
