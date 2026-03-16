"""Integration test: JSON file to Terraform output.

Spec: Input is JSON (not Markdown). See tests/TEST_SPECS.md for full coverage requirements.
"""

from pathlib import Path

import pytest

from terraform_generator.config import Settings
from terraform_generator.events.orchestrator import Orchestrator
from terraform_generator.events.payloads import ProcessingCompletedPayload, ProcessingFailedPayload


def test_pipeline_empty_array_returns_failed():
    """Empty array returns ProcessingFailedPayload."""
    fixture = Path(__file__).parent.parent / "fixtures" / "sample_inputs" / "invalid_empty_array.json"
    if not fixture.exists():
        pytest.skip("Fixture not found")

    settings = Settings.model_construct(environment="dev", output_dir=Path("/tmp/tfgen_test_output"))
    orchestrator = Orchestrator(settings=settings)
    result = orchestrator.process(file_path=fixture)

    assert isinstance(result, ProcessingFailedPayload)
    assert result.stage == "input_validation"


def test_pipeline_item_without_output_returns_failed():
    """Item without output returns ProcessingFailedPayload."""
    fixture = Path(__file__).parent.parent / "fixtures" / "sample_inputs" / "invalid_item_without_output.json"
    if not fixture.exists():
        pytest.skip("Fixture not found")

    settings = Settings.model_construct(environment="dev", output_dir=Path("/tmp/tfgen_test_output"))
    orchestrator = Orchestrator(settings=settings)
    result = orchestrator.process(file_path=fixture)

    assert isinstance(result, ProcessingFailedPayload)
    assert result.stage == "input_validation"


def test_pipeline_object_root_returns_ingestion_error():
    """Object at root (old format) returns ingestion error."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"analise_entrada": "test"}')
        tmp_path = f.name

    try:
        settings = Settings.model_construct(environment="dev", output_dir=Path("/tmp/tfgen_test_output"))
        orchestrator = Orchestrator(settings=settings)
        result = orchestrator.process(file_path=tmp_path)
        assert isinstance(result, ProcessingFailedPayload)
        assert result.stage == "ingestion"
        assert "array" in result.error.lower()
    finally:
        import os
        os.unlink(tmp_path)


def test_pipeline_invalid_json_returns_failed():
    """Invalid JSON (missing analise_entrada in output) returns ProcessingFailedPayload."""
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
    """Full pipeline: web_app.json with decision=vibe_economica -> Terraform files.

    Input: JSON with both vibes; decision selects vibe_economica only.
    Expected: ProcessingCompletedPayload with 3 resources (S3, security group, instance).
    """
    fixture = Path(__file__).parent.parent / "fixtures" / "sample_inputs" / "web_app.json"
    if not fixture.exists():
        pytest.skip("Fixture not found: web_app.json")

    settings = Settings.model_construct(
        environment="dev",
        output_dir=Path("/tmp/tfgen_test_output"),
    )
    orchestrator = Orchestrator(settings=settings)
    result = orchestrator.process(file_path=fixture, decision="vibe_economica")

    assert isinstance(result, ProcessingCompletedPayload), (
        f"Expected ProcessingCompletedPayload, got {type(result).__name__}"
    )
    # vibe_economica has exactly 3 resources: S3, security group, instance
    assert result.summary["resources"] == 3
    assert result.summary["files"] >= 4

    output_path = Path(result.output_path)
    assert output_path.exists(), f"Output path should exist: {output_path}"
    assert (output_path / "main.tf").exists()
    assert (output_path / "s3_buckets.tf").exists()
    assert (output_path / "security_groups.tf").exists()
    assert (output_path / "instances.tf").exists()


def test_pipeline_decision_vibe_economica_generates_only_economic_resources():
    """decision=vibe_economica generates only vibe_economica resources (3)."""
    fixture = Path(__file__).parent.parent / "fixtures" / "sample_inputs" / "web_app.json"
    if not fixture.exists():
        pytest.skip("Fixture not found")

    settings = Settings.model_construct(environment="dev", output_dir=Path("/tmp/tfgen_test_output"))
    orchestrator = Orchestrator(settings=settings)
    result = orchestrator.process(file_path=fixture, decision="vibe_economica")

    assert isinstance(result, ProcessingCompletedPayload)
    assert result.summary["resources"] == 3


def test_pipeline_decision_vibe_performance_generates_only_performance_resources():
    """decision=vibe_performance generates only vibe_performance resources (2)."""
    fixture = Path(__file__).parent.parent / "fixtures" / "sample_inputs" / "web_app.json"
    if not fixture.exists():
        pytest.skip("Fixture not found")

    settings = Settings.model_construct(environment="dev", output_dir=Path("/tmp/tfgen_test_output"))
    orchestrator = Orchestrator(settings=settings)
    result = orchestrator.process(file_path=fixture, decision="vibe_performance")

    assert isinstance(result, ProcessingCompletedPayload)
    assert result.summary["resources"] == 2


def test_pipeline_invalid_decision_returns_failed():
    """Invalid decision returns ProcessingFailedPayload."""
    fixture = Path(__file__).parent.parent / "fixtures" / "sample_inputs" / "web_app.json"
    if not fixture.exists():
        pytest.skip("Fixture not found")

    settings = Settings.model_construct(environment="dev", output_dir=Path("/tmp/tfgen_test_output"))
    orchestrator = Orchestrator(settings=settings)
    result = orchestrator.process(file_path=fixture, decision="invalid_vibe")

    assert isinstance(result, ProcessingFailedPayload)
    assert result.stage == "input_validation"
    assert "Invalid decision" in result.error


def test_pipeline_chosen_vibe_missing_returns_failed():
    """When chosen vibe does not exist in payload, returns ProcessingFailedPayload."""
    fixture = Path(__file__).parent.parent / "fixtures" / "sample_inputs" / "vibe_economica_only.json"
    if not fixture.exists():
        pytest.skip("Fixture not found")

    settings = Settings.model_construct(environment="dev", output_dir=Path("/tmp/tfgen_test_output"))
    orchestrator = Orchestrator(settings=settings)
    result = orchestrator.process(file_path=fixture, decision="vibe_performance")

    assert isinstance(result, ProcessingFailedPayload)
    assert result.stage == "input_validation"
    assert "not found" in result.error.lower()


def test_pipeline_no_decision_processes_both_vibes():
    """When decision is omitted, both vibes are processed (CLI backward compat)."""
    fixture = Path(__file__).parent.parent / "fixtures" / "sample_inputs" / "web_app.json"
    if not fixture.exists():
        pytest.skip("Fixture not found")

    settings = Settings.model_construct(environment="dev", output_dir=Path("/tmp/tfgen_test_output"))
    orchestrator = Orchestrator(settings=settings)
    result = orchestrator.process(file_path=fixture)

    assert isinstance(result, ProcessingCompletedPayload)
    # Both vibes: 3 + 2 = 5 resources
    assert result.summary["resources"] == 5
