"""Unit tests for input extractor."""

import pytest

from terraform_generator.domain.exceptions import InputValidationError
from terraform_generator.input.extractor import extract_architecture_payload


def test_extract_valid_payload():
    """Extract output from first item."""
    data = [{"output": {"analise_entrada": "test", "vibe_economica": {"recursos": []}}}]
    result = extract_architecture_payload(data)
    assert result["analise_entrada"] == "test"
    assert "vibe_economica" in result


def test_extract_rejects_empty_array():
    """Reject empty array."""
    with pytest.raises(InputValidationError, match="non-empty"):
        extract_architecture_payload([])


def test_extract_rejects_item_without_output():
    """Reject item missing output."""
    with pytest.raises(InputValidationError, match="output"):
        extract_architecture_payload([{"other": "field"}])


def test_extract_rejects_output_not_object():
    """Reject when output is not an object."""
    with pytest.raises(InputValidationError, match="output.*object"):
        extract_architecture_payload([{"output": "string"}])


def test_extract_uses_first_item_only():
    """Only first item's output is extracted (pipeline processes one at a time)."""
    data = [
        {"output": {"analise_entrada": "first"}},
        {"output": {"analise_entrada": "second"}},
    ]
    result = extract_architecture_payload(data)
    assert result["analise_entrada"] == "first"
