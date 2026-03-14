"""Integration test: JSON file to Terraform output.

Spec: Input is JSON (not Markdown). See tests/TEST_SPECS.md for full coverage requirements.
"""

from pathlib import Path

import pytest

from terraform_generator.config import Settings
from terraform_generator.events.orchestrator import Orchestrator
from terraform_generator.events.payloads import ProcessingCompletedPayload, ProcessingFailedPayload


def test_pipeline_invalid_json_returns_failed():
    """Invalid JSON (missing analise_entrada) returns ProcessingFailedPayload."""
    fixture = Path(__file__).parent.parent / "fixtures" / "sample_inputs" / "invalid_missing_analise.json"
    if not fixture.exists():
        pytest.skip("Fixture not found")

    settings = Settings.model_construct(environment="dev", output_dir=Path("/tmp/tfgen_test_output"))
    orchestrator = Orchestrator(settings=settings)
    result = orchestrator.process(file_path=fixture)

    assert isinstance(result, ProcessingFailedPayload)
    assert result.stage == "input_validation"


def test_pipeline_unsupported_service_returns_failed():
    """JSON with unsupported service returns ProcessingFailedPayload."""
    fixture = Path(__file__).parent.parent / "fixtures" / "sample_inputs" / "invalid_unsupported_service.json"
    if not fixture.exists():
        pytest.skip("Fixture not found")

    settings = Settings.model_construct(environment="dev", output_dir=Path("/tmp/tfgen_test_output"))
    orchestrator = Orchestrator(settings=settings)
    result = orchestrator.process(file_path=fixture)

    assert isinstance(result, ProcessingFailedPayload)
    assert result.stage in ("input_validation", "normalization")


def test_pipeline_web_app():
    """Full pipeline: web_app.json -> Terraform files.

    Input: JSON with analise_entrada, vibe_economica (S3, security group, instance).
    Expected: ProcessingCompletedPayload; output dir contains main.tf, s3_buckets.tf,
    security_groups.tf, instances.tf.
    """
    fixture = Path(__file__).parent.parent / "fixtures" / "sample_inputs" / "web_app.json"
    if not fixture.exists():
        pytest.skip("Fixture not found: web_app.json")

    # Use model_construct to force dev mode (avoids .env ENVIRONMENT=production)
    settings = Settings.model_construct(
        environment="dev",
        output_dir=Path("/tmp/tfgen_test_output"),
    )
    orchestrator = Orchestrator(settings=settings)
    result = orchestrator.process(file_path=fixture)

    assert isinstance(result, ProcessingCompletedPayload), (
        f"Expected ProcessingCompletedPayload, got {type(result).__name__}"
    )
    # web_app.json vibe_economica has 3 resources: S3, security group, instance
    assert result.summary["resources"] >= 3
    assert result.summary["files"] >= 4

    output_path = Path(result.output_path)
    assert output_path.exists(), f"Output path should exist: {output_path}"
    assert (output_path / "main.tf").exists()
    assert (output_path / "s3_buckets.tf").exists()
    assert (output_path / "security_groups.tf").exists()
    assert (output_path / "instances.tf").exists()
