"""Unit tests for vibe selection."""

import pytest

from terraform_generator.domain.exceptions import InputValidationError
from terraform_generator.input.vibe_selector import select_chosen_vibe


def test_select_vibe_economica():
    """Select vibe_economica returns payload with only that vibe."""
    payload = {
        "analise_entrada": "test",
        "vibe_economica": {"recursos": [{"servico": "aws_s3_bucket", "config": {"bucket": "a"}}]},
        "vibe_performance": {"recursos": [{"servico": "aws_instance", "config": {}}]},
    }
    result = select_chosen_vibe(payload, "vibe_economica")
    assert "vibe_economica" in result
    assert "vibe_performance" not in result
    assert result["analise_entrada"] == "test"
    assert len(result["vibe_economica"]["recursos"]) == 1
    assert result["vibe_economica"]["recursos"][0]["servico"] == "aws_s3_bucket"


def test_select_vibe_performance():
    """Select vibe_performance returns payload with only that vibe."""
    payload = {
        "analise_entrada": "test",
        "vibe_economica": {"recursos": []},
        "vibe_performance": {"recursos": [{"servico": "aws_instance", "config": {}}]},
    }
    result = select_chosen_vibe(payload, "vibe_performance")
    assert "vibe_performance" in result
    assert "vibe_economica" not in result
    assert len(result["vibe_performance"]["recursos"]) == 1


def test_select_rejects_invalid_decision():
    """Invalid decision raises InputValidationError."""
    payload = {"analise_entrada": "test", "vibe_economica": {"recursos": []}}
    with pytest.raises(InputValidationError, match="Invalid decision"):
        select_chosen_vibe(payload, "invalid")


def test_select_rejects_missing_vibe():
    """Chosen vibe missing from payload raises InputValidationError."""
    payload = {"analise_entrada": "test", "vibe_economica": {"recursos": []}}
    with pytest.raises(InputValidationError, match="not found"):
        select_chosen_vibe(payload, "vibe_performance")


def test_select_rejects_vibe_not_dict():
    """Chosen vibe not a dict raises InputValidationError."""
    payload = {"analise_entrada": "test", "vibe_economica": "not a dict"}
    with pytest.raises(InputValidationError, match="not found or invalid"):
        select_chosen_vibe(payload, "vibe_economica")


def test_select_rejects_empty_vibe():
    """Chosen vibe missing (None) raises InputValidationError."""
    payload = {"analise_entrada": "test"}
    with pytest.raises(InputValidationError, match="not found"):
        select_chosen_vibe(payload, "vibe_economica")
