"""Integration test: MD file to Terraform output."""

from pathlib import Path

import pytest

from terraform_generator.config import Settings
from terraform_generator.events.orchestrator import Orchestrator
from terraform_generator.events.payloads import ProcessingCompletedPayload, ProcessingFailedPayload


def test_pipeline_web_app():
    """Full pipeline: web_app.md -> Terraform files."""
    fixture = Path(__file__).parent.parent / "fixtures" / "sample_architectures" / "web_app.md"
    if not fixture.exists():
        pytest.skip("Fixture not found")

    settings = Settings(output_dir=Path("/tmp/tfgen_test_output"))
    orchestrator = Orchestrator(settings=settings)
    result = orchestrator.process(file_path=fixture)

    assert isinstance(result, ProcessingCompletedPayload)
    assert result.summary["resources"] == 3
    assert result.summary["files"] >= 4

    output_path = Path(result.output_path)
    assert output_path.exists()
    assert (output_path / "main.tf").exists()
    assert (output_path / "s3_buckets.tf").exists()
    assert (output_path / "security_groups.tf").exists()
    assert (output_path / "instances.tf").exists()
