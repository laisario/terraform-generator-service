"""Unit tests for JSON ingestion."""

from pathlib import Path

import pytest

from terraform_generator.config import Settings
from terraform_generator.domain.exceptions import IngestionError
from terraform_generator.ingestion.loader import Loader


def test_load_from_path_valid_json(tmp_path):
    """Load valid JSON from file path."""
    json_file = tmp_path / "input.json"
    json_file.write_text('{"analise_entrada": "test", "vibe_economica": {"recursos": []}}')

    loader = Loader(Settings())
    data = loader.load_from_path(json_file)

    assert data["analise_entrada"] == "test"
    assert "vibe_economica" in data
    assert data["vibe_economica"]["recursos"] == []


def test_load_from_path_file_not_found():
    """Raise IngestionError when file does not exist."""
    loader = Loader()
    with pytest.raises(IngestionError, match="File not found"):
        loader.load_from_path("/nonexistent/path.json")


def test_load_from_content_valid_json():
    """Load valid JSON from string content."""
    content = '{"analise_entrada": "from stdin"}'
    loader = Loader()
    data = loader.load_from_content(content)
    assert data["analise_entrada"] == "from stdin"


def test_load_from_content_invalid_json():
    """Raise IngestionError for invalid JSON."""
    loader = Loader()
    with pytest.raises(IngestionError, match="Invalid JSON"):
        loader.load_from_content("{ invalid json }")


def test_load_from_content_not_object():
    """Raise IngestionError when JSON is not an object."""
    loader = Loader()
    with pytest.raises(IngestionError, match="Expected JSON object"):
        loader.load_from_content('["array", "not", "object"]')
