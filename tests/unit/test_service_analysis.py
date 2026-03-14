"""Unit tests for service analysis."""

import pytest

from terraform_generator.domain.exceptions import InputValidationError
from terraform_generator.input.analyzer import InputAnalyzer


def test_analyze_vibe_economica_only():
    """Extract resources from vibe_economica only."""
    data = {
        "analise_entrada": "test",
        "vibe_economica": {
            "recursos": [
                {"servico": "aws_s3_bucket", "config": {"bucket": "my-bucket"}},
            ],
        },
    }
    analyzer = InputAnalyzer()
    raw = analyzer.analyze(data)
    assert len(raw) == 1
    assert raw[0].type == "aws_s3_bucket"
    assert raw[0].attributes["bucket"] == "my-bucket"
    assert raw[0].logical_name  # generated


def test_analyze_vibe_performance_only():
    """Extract resources from vibe_performance only."""
    data = {
        "analise_entrada": "test",
        "vibe_performance": {
            "recursos": [
                {"servico": "aws_instance", "config": {"ami": "ami-123", "instance_type": "t3.micro"}},
            ],
        },
    }
    analyzer = InputAnalyzer()
    raw = analyzer.analyze(data)
    assert len(raw) == 1
    assert raw[0].type == "aws_instance"
    assert raw[0].attributes["ami"] == "ami-123"


def test_analyze_merges_both_vibes():
    """Merge resources from both vibe_economica and vibe_performance."""
    data = {
        "analise_entrada": "test",
        "vibe_economica": {"recursos": [{"servico": "aws_s3_bucket", "config": {"bucket": "a"}}]},
        "vibe_performance": {"recursos": [{"servico": "aws_s3_bucket", "config": {"bucket": "b"}}]},
    }
    analyzer = InputAnalyzer()
    raw = analyzer.analyze(data)
    assert len(raw) == 2
    assert raw[0].attributes["bucket"] == "a"
    assert raw[1].attributes["bucket"] == "b"


def test_analyze_rejects_unsupported_service():
    """Reject unsupported service in recursos."""
    data = {
        "analise_entrada": "test",
        "vibe_economica": {
            "recursos": [{"servico": "aws_lambda_function", "config": {}}],
        },
    }
    analyzer = InputAnalyzer()
    with pytest.raises(InputValidationError, match="Unsupported service"):
        analyzer.analyze(data)


def test_analyze_empty_recursos():
    """Return empty list when no recursos."""
    data = {"analise_entrada": "test", "vibe_economica": {"recursos": []}}
    analyzer = InputAnalyzer()
    raw = analyzer.analyze(data)
    assert raw == []


def test_analyze_config_as_string():
    """Handle config as string (converted to dict with raw key)."""
    data = {
        "analise_entrada": "test",
        "vibe_economica": {
            "recursos": [{"servico": "aws_s3_bucket", "config": "raw config string"}],
        },
    }
    analyzer = InputAnalyzer()
    raw = analyzer.analyze(data)
    assert len(raw) == 1
    assert raw[0].attributes.get("raw") == "raw config string"
