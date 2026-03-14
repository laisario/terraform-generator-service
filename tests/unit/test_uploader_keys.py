"""Unit tests for uploader object key generation."""

from unittest.mock import MagicMock, patch

from terraform_generator.config import Settings
from terraform_generator.storage.uploader import ArtifactUploader


def test_object_key_preserves_output_structure():
    """Object key must be output/<job_id>/<file_name>."""
    settings = Settings.model_construct(
        s3_api_url="https://test.r2.cloudflarestorage.com",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    uploader = ArtifactUploader(settings=settings)

    files = [
        ("main.tf", "terraform {}"),
        ("instances.tf", "resource {}"),
    ]
    job_id = "596f3f2f-29b8-4359-b179-0fb667b7c272"

    mock_client = MagicMock()
    with patch("boto3.client", return_value=mock_client):
        result = uploader.upload_from_content(files, job_id)

    assert "output/596f3f2f-29b8-4359-b179-0fb667b7c272/main.tf" in result
    assert "output/596f3f2f-29b8-4359-b179-0fb667b7c272/instances.tf" in result
    assert len(result) == 2

    # Verify put_object was called with correct object keys
    calls = mock_client.put_object.call_args_list
    keys = [c[1]["Key"] for c in calls]
    assert "output/596f3f2f-29b8-4359-b179-0fb667b7c272/main.tf" in keys
    assert "output/596f3f2f-29b8-4359-b179-0fb667b7c272/instances.tf" in keys
