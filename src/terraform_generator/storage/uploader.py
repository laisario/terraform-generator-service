"""Upload generated Terraform files to S3-compatible object storage."""

import logging

from terraform_generator.config import Settings
from terraform_generator.domain.exceptions import UploadError
from terraform_generator.storage.paths import build_object_key

logger = logging.getLogger(__name__)


class ArtifactUploader:
    """Upload Terraform files to S3-compatible storage (Cloudflare R2)."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()

    def upload_from_content(
        self,
        files: list[tuple[str, str]],
        job_id: str,
    ) -> list[str]:
        """
        Upload files directly to S3 from content (no local disk).
        Object key: output/<job_id>/<filename>

        Returns list of uploaded object keys.
        Raises UploadError on failure.
        """
        try:
            import boto3
            from botocore.config import Config
        except ImportError as err:
            raise UploadError(
                "boto3 is required for artifact upload. Install with: pip install boto3"
            ) from err

        if not self.settings.s3_api_url:
            raise UploadError(
                "S3_API endpoint not configured. Set S3_API in .env for production uploads."
            )

        if not self.settings.aws_access_key_id or not self.settings.aws_secret_access_key:
            raise UploadError(
                "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set in .env for production uploads."
            )

        file_count = len(files)
        logger.info(
            "Upload started (direct to S3)",
            extra={"job_id": job_id, "file_count": file_count},
        )

        endpoint = self.settings.s3_api_url.rstrip("/")
        use_ssl = endpoint.startswith("https")

        client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            region_name="auto",
            aws_access_key_id=self.settings.aws_access_key_id,
            aws_secret_access_key=self.settings.aws_secret_access_key,
            config=Config(signature_version="s3v4"),
            use_ssl=use_ssl,
        )

        uploaded_keys: list[str] = []
        bucket = self.settings.storage_bucket

        for filename, content in sorted(files):
            object_key = build_object_key(job_id, filename)

            try:
                client.put_object(
                    Bucket=bucket,
                    Key=object_key,
                    Body=content.encode("utf-8"),
                )
                uploaded_keys.append(object_key)
                logger.info(
                    "File uploaded",
                    extra={"job_id": job_id, "object_key": object_key},
                )
            except Exception as e:
                logger.error(
                    "Upload failed",
                    extra={
                        "job_id": job_id,
                        "object_key": object_key,
                        "error": str(e),
                        "partial_uploads": uploaded_keys,
                    },
                )
                err = UploadError(
                    f"Failed to upload {filename}: {e}. "
                    f"Partial uploads: {uploaded_keys}"
                )
                err.partial_uploads = uploaded_keys  # type: ignore[attr-defined]
                raise err from e

        logger.info(
            "Upload completed",
            extra={"job_id": job_id, "object_keys": uploaded_keys},
        )
        return uploaded_keys
