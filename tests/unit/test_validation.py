"""Unit tests for validation."""

import pytest

from terraform_generator.domain.models import Architecture, InfrastructureResource
from terraform_generator.validation.validator import Validator


def test_validate_valid_architecture():
    """Valid architecture passes validation."""
    arch = Architecture(
        id="test",
        provider="aws",
        resources=[
            InfrastructureResource(
                type="aws_s3_bucket",
                logical_name="main",
                attributes={"bucket": "my-bucket"},
            ),
        ],
    )
    validator = Validator()
    result = validator.validate(arch)
    assert result.valid
    assert len(result.errors) == 0


def test_validate_missing_required_attribute():
    """Missing required attribute fails validation."""
    arch = Architecture(
        id="test",
        provider="aws",
        resources=[
            InfrastructureResource(
                type="aws_s3_bucket",
                logical_name="main",
                attributes={},  # missing bucket
            ),
        ],
    )
    validator = Validator()
    result = validator.validate(arch)
    assert not result.valid
    assert any(e.code == "missing_required_attribute" for e in result.errors)


def test_validate_empty_resources_warning():
    """Empty resources produces warning."""
    arch = Architecture(id="test", provider="aws", resources=[])
    validator = Validator()
    result = validator.validate(arch)
    assert result.valid  # warnings don't block
    assert any(w.code == "empty_resources" for w in result.warnings)
