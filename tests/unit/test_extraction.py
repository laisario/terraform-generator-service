"""Unit tests for extraction."""

import pytest

from terraform_generator.extraction.extractor import Extractor
from terraform_generator.parsing.blocks import BlockType
from terraform_generator.parsing.markdown_parser import MarkdownParser


def test_extract_s3_bucket():
    """Extract aws_s3_bucket from HCL block."""
    content = """# Arch

```terraform
resource "aws_s3_bucket" "main_bucket" {
  bucket = "my-app-bucket"
}
```
"""
    parser = MarkdownParser()
    blocks = parser.parse(content)
    extractor = Extractor()
    raw = extractor.extract(blocks)

    assert len(raw) == 1
    assert raw[0].type == "aws_s3_bucket"
    assert raw[0].logical_name == "main_bucket"
    assert raw[0].attributes.get("bucket") == "my-app-bucket"


def test_extract_multiple_resources():
    """Extract multiple resources from one block."""
    content = """```terraform
resource "aws_s3_bucket" "a" { bucket = "a" }
resource "aws_instance" "b" { ami = "ami-123" instance_type = "t3.micro" }
```
"""
    parser = MarkdownParser()
    blocks = parser.parse(content)
    extractor = Extractor()
    raw = extractor.extract(blocks)

    assert len(raw) == 2
    assert raw[0].type == "aws_s3_bucket" and raw[0].logical_name == "a"
    assert raw[1].type == "aws_instance" and raw[1].logical_name == "b"
