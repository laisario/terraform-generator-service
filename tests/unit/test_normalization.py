"""Unit tests for normalization."""

import pytest

from terraform_generator.domain.models import Architecture, RawRequirement
from terraform_generator.normalization.normalizer import Normalizer
from terraform_generator.domain.exceptions import NormalizationError


def test_normalize_simple():
    """Normalize raw requirements to Architecture."""
    raw = [
        RawRequirement("aws_s3_bucket", "main", {"bucket": "my-bucket"}),
    ]
    normalizer = Normalizer("test-123")
    arch = normalizer.normalize(raw)

    assert arch.id == "test-123"
    assert arch.provider == "aws"
    assert len(arch.resources) == 1
    assert arch.resources[0].type == "aws_s3_bucket"
    assert arch.resources[0].logical_name == "main"
    assert arch.resources[0].attributes["bucket"] == "my-bucket"


def test_normalize_rejects_unsupported_type():
    """Reject unsupported resource type."""
    raw = [RawRequirement("aws_lambda_function", "fn", {})]
    normalizer = Normalizer("test-123")
    with pytest.raises(NormalizationError, match="Unsupported resource type"):
        normalizer.normalize(raw)


def test_normalize_rejects_duplicate_logical_name():
    """Reject duplicate logical names."""
    raw = [
        RawRequirement("aws_s3_bucket", "dup", {"bucket": "a"}),
        RawRequirement("aws_s3_bucket", "dup", {"bucket": "b"}),
    ]
    normalizer = Normalizer("test-123")
    with pytest.raises(NormalizationError, match="Duplicate logical_name"):
        normalizer.normalize(raw)
