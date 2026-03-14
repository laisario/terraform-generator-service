"""Centralized path and object key construction for artifact storage."""

from pathlib import Path

# Root prefix for output - used for both local paths and S3 object keys
OUTPUT_ROOT = "output"


def build_object_key(job_id: str, filename: str) -> str:
    """
    Build S3 object key that mirrors local structure.
    Result: output/<job_id>/<filename>
    """
    key = Path(OUTPUT_ROOT) / job_id / filename
    return key.as_posix()


def build_local_job_dir(output_root: Path, job_id: str) -> Path:
    """Build local job directory path: output_root/<job_id>/"""
    return Path(output_root) / job_id


def build_output_path(output_root: Path, job_id: str, filename: str) -> Path:
    """Build full local file path: output_root/<job_id>/<filename>"""
    return build_local_job_dir(output_root, job_id) / filename
