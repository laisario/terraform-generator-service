"""Unit tests for storage path/key construction."""

from pathlib import Path

from terraform_generator.storage.paths import (
    build_local_job_dir,
    build_object_key,
    build_output_path,
)


def test_build_object_key():
    """Object key must be output/<job_id>/<filename>."""
    key = build_object_key("596f3f2f-29b8-4359-b179-0fb667b7c272", "instances.tf")
    assert key == "output/596f3f2f-29b8-4359-b179-0fb667b7c272/instances.tf"


def test_build_local_job_dir():
    """Local job dir is output_root/<job_id>/"""
    job_dir = build_local_job_dir(Path("/tmp/output"), "job-123")
    assert job_dir == Path("/tmp/output/job-123")


def test_build_output_path():
    """Full local path is output_root/<job_id>/<filename>"""
    path = build_output_path(Path("/tmp/output"), "job-123", "main.tf")
    assert path == Path("/tmp/output/job-123/main.tf")
