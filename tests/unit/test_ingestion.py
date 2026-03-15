"""Unit tests for JSON ingestion."""

from pathlib import Path

import pytest

from terraform_generator.config import Settings
from terraform_generator.domain.exceptions import IngestionError
from terraform_generator.ingestion.loader import Loader


def test_load_from_path_valid_array(tmp_path):
    """Load valid JSON array from file path."""
    json_file = tmp_path / "input.json"
    json_file.write_text('[{"output": {"analise_entrada": "test", "vibe_economica": {"recursos": []}}}]')

    loader = Loader(Settings())
    data = loader.load_from_path(json_file)

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["output"]["analise_entrada"] == "test"
    assert data[0]["output"]["vibe_economica"]["recursos"] == []


def test_load_from_path_file_not_found():
    """Raise IngestionError when file does not exist."""
    loader = Loader()
    with pytest.raises(IngestionError, match="File not found"):
        loader.load_from_path("/nonexistent/path.json")


def test_load_from_content_valid_array():
    """Load valid JSON array from string content."""
    content = '[{"output": {"analise_entrada": "from stdin"}}]'
    loader = Loader()
    data = loader.load_from_content(content)
    assert isinstance(data, list)
    assert data[0]["output"]["analise_entrada"] == "from stdin"


def test_load_from_content_invalid_json():
    """Raise IngestionError for invalid JSON."""
    loader = Loader()
    with pytest.raises(IngestionError, match="Invalid JSON"):
        loader.load_from_content("{ invalid json }")


def test_load_from_content_rejects_object_root():
    """Raise IngestionError when root is object instead of array."""
    loader = Loader()
    with pytest.raises(IngestionError, match="Root input must be a JSON array"):
        loader.load_from_content('{"analise_entrada": "test"}')
