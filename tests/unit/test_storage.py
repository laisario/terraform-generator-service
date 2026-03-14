"""Unit tests for artifact storage."""

from pathlib import Path
from unittest.mock import patch

import pytest

from terraform_generator.config import Settings
from terraform_generator.domain.exceptions import UploadError
from terraform_generator.storage.handler import StorageHandler
from terraform_generator.storage.uploader import ArtifactUploader


def test_storage_handler_dev_mode_local_only(tmp_path):
    """In dev mode, persist writes locally and returns success without uploading."""
    settings = Settings.model_construct(environment="dev", output_dir=tmp_path)
    handler = StorageHandler(settings=settings)

    files = [("main.tf", "terraform {}")]
    success, object_keys = handler.persist(files, "job-123")

    assert success is True
    assert object_keys is None
    assert (tmp_path / "job-123" / "main.tf").exists()
    assert (tmp_path / "job-123" / "main.tf").read_text() == "terraform {}"


def test_storage_handler_production_fails_without_s3_config():
    """In production without S3_API, upload raises and handler returns failure."""
    settings = Settings.model_construct(
        environment="production",
        s3_api_url=None,
    )
    handler = StorageHandler(settings=settings)

    files = [("main.tf", "terraform {}")]
    success, object_keys = handler.persist(files, "job-123")

    assert success is False
    assert object_keys == []


def test_storage_handler_production_upload_success(tmp_path):
    """In production with mocked upload, succeeds and returns object keys. No local write."""
    settings = Settings.model_construct(
        environment="production",
        s3_api_url="https://test.r2.cloudflarestorage.com",
    )
    handler = StorageHandler(settings=settings)

    files = [("main.tf", "terraform {}"), ("s3.tf", "resource {}")]

    with patch.object(handler.uploader, "upload_from_content") as mock_upload:
        mock_upload.return_value = [
            "output/job-123/main.tf",
            "output/job-123/s3.tf",
        ]
        success, object_keys = handler.persist(files, "job-123")

    assert success is True
    assert object_keys == ["output/job-123/main.tf", "output/job-123/s3.tf"]
    mock_upload.assert_called_once_with(files, "job-123")
    # Production must NOT write locally
    assert not (tmp_path / "job-123").exists()


def test_storage_handler_production_upload_failure_returns_partial():
    """In production when upload fails, returns partial_uploads."""
    settings = Settings.model_construct(
        environment="production",
        s3_api_url="https://test.r2.cloudflarestorage.com",
    )
    handler = StorageHandler(settings=settings)

    err = UploadError("Upload failed")
    err.partial_uploads = ["output/job-123/main.tf"]  # type: ignore[attr-defined]

    files = [("main.tf", "terraform {}")]

    with patch.object(handler.uploader, "upload_from_content", side_effect=err):
        success, object_keys = handler.persist(files, "job-123")

    assert success is False
    assert object_keys == ["output/job-123/main.tf"]


def test_uploader_requires_s3_api():
    """Uploader raises UploadError when S3_API is not configured."""
    settings = Settings.model_construct(s3_api_url=None)
    uploader = ArtifactUploader(settings=settings)

    with pytest.raises(UploadError, match="S3_API"):
        uploader.upload_from_content([("main.tf", "x")], "job-123")
