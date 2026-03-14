"""Storage handler - branches on ENVIRONMENT (dev vs production)."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from terraform_generator.config import Settings
from terraform_generator.domain.exceptions import UploadError
from terraform_generator.storage.paths import build_local_job_dir
from terraform_generator.storage.uploader import ArtifactUploader

if TYPE_CHECKING:
    from terraform_generator.terraform.writer import TerraformWriter

logger = logging.getLogger(__name__)


class StorageHandler:
    """
    Persist artifacts based on ENVIRONMENT:
    - dev: local disk only (output/<job_id>/)
    - production: S3 only (no local persistence)
    """

    def __init__(
        self,
        settings: Settings | None = None,
        writer: "TerraformWriter | None" = None,
    ) -> None:
        self.settings = settings or Settings()
        self.uploader = ArtifactUploader(self.settings)
        self._writer = writer

    def _get_writer(self) -> "TerraformWriter":
        if self._writer is None:
            from terraform_generator.terraform.writer import TerraformWriter
            return TerraformWriter(self.settings)
        return self._writer

    def persist(
        self,
        files: list[tuple[str, str]],
        job_id: str,
    ) -> tuple[bool, list[str] | None]:
        """
        Persist artifacts based on ENVIRONMENT.

        Returns (success, object_keys).
        - dev: writes to output/<job_id>/, success=True, object_keys=None
        - production: uploads to S3 only (no local write), success=True, object_keys=[...]
        - production failure: success=False, object_keys=partial_uploads or []
        """
        env = self.settings.environment.lower()
        logger.info(
            "Storage strategy: %s (ENVIRONMENT=%s)",
            "local only" if env == "dev" else "S3 only",
            env,
            extra={"job_id": job_id},
        )

        if env == "dev":
            job_dir = build_local_job_dir(self.settings.output_dir, job_id)
            self._get_writer().write(job_dir, files)
            logger.info(
                "Artifacts written locally (ENVIRONMENT=dev)",
                extra={"job_id": job_id, "path": str(job_dir)},
            )
            return True, None

        if env == "production":
            try:
                object_keys = self.uploader.upload_from_content(files, job_id)
                return True, object_keys
            except Exception as e:
                partial = getattr(e, "partial_uploads", []) if isinstance(e, UploadError) else []
                logger.error(
                    "Upload failed: %s",
                    e,
                    extra={"job_id": job_id, "partial_uploads": partial},
                )
                return False, partial

        # Unknown environment - treat as dev (local only)
        logger.warning(
            "Unknown ENVIRONMENT=%s, using local storage only",
            env,
            extra={"job_id": job_id},
        )
        job_dir = build_local_job_dir(self.settings.output_dir, job_id)
        self._get_writer().write(job_dir, files)
        return True, None
