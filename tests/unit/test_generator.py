"""Unit tests for Terraform generator."""

from terraform_generator.domain.models import Architecture, InfrastructureResource
from terraform_generator.terraform.generator import TerraformGenerator


def test_generate_s3_bucket():
    """Generate Terraform for S3 bucket."""
    arch = Architecture(
        id="test",
        provider="aws",
        resources=[
            InfrastructureResource(
                type="aws_s3_bucket",
                logical_name="assets",
                attributes={"bucket": "my-assets"},
            ),
        ],
    )
    gen = TerraformGenerator()
    files = gen.generate(arch)

    assert any(name == "main.tf" for name, _ in files)
    assert any(name == "s3_buckets.tf" for name, _ in files)

    s3_content = next(c for n, c in files if n == "s3_buckets.tf")
    assert "aws_s3_bucket" in s3_content
    assert "assets" in s3_content
    assert "my-assets" in s3_content


def test_generate_main_tf():
    """main.tf contains provider block."""
    arch = Architecture(id="test", provider="aws", resources=[])
    gen = TerraformGenerator()
    files = gen.generate(arch)

    main = next(c for n, c in files if n == "main.tf")
    assert "hashicorp/aws" in main
    assert "provider \"aws\"" in main
