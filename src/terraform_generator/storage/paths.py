"""Centralized path and object key construction for artifact storage."""

from pathlib import Path

# Root prefix for output - used for both local paths and S3 object keys
OUTPUT_ROOT = "output"


def build_object_key(job_id: str, filename: str) -> str:
    """
    Build S3 object key that mirrors local directory structure.

    S3 uses the key as the full path; slashes create logical hierarchy.
    Result: output/<job_id>/<filename>

    Example: output/c8883521-f871-4d3b-a9f6-16affcdd54ba/main.tf
    """
    safe_filename = Path(filename).name
    return f"{OUTPUT_ROOT}/{job_id}/{safe_filename}"


def build_local_job_dir(output_root: Path, job_id: str) -> Path:
    """Build local job directory path: output_root/<job_id>/"""
    return Path(output_root) / job_id


def build_output_path(output_root: Path, job_id: str, filename: str) -> Path:
    """Build full local file path: output_root/<job_id>/<filename>"""
    return build_local_job_dir(output_root, job_id) / filename
