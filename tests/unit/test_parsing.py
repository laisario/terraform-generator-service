"""Unit tests for parsing."""

import pytest

from terraform_generator.parsing.blocks import BlockType, CodeBlock, Heading
from terraform_generator.parsing.markdown_parser import MarkdownParser


def test_parse_headings_and_code_block():
    """Parse MD with headings and terraform code block."""
    content = """# My Architecture

## S3

```terraform
resource "aws_s3_bucket" "main" {
  bucket = "my-bucket"
}
```
"""
    parser = MarkdownParser()
    blocks = parser.parse(content)

    assert len(blocks) >= 3
    assert blocks[0][0] == BlockType.HEADING
    assert blocks[0][1].level == 1
    assert blocks[0][1].text == "My Architecture"

    assert blocks[1][0] == BlockType.HEADING
    assert blocks[1][1].level == 2
    assert blocks[1][1].text == "S3"

    assert blocks[2][0] == BlockType.CODE_BLOCK
    assert blocks[2][1].language == "terraform"
    assert "aws_s3_bucket" in blocks[2][1].content
    assert "main" in blocks[2][1].content


def test_parse_hcl_language():
    """Code block with hcl language is identified."""
    content = """```hcl
resource "aws_instance" "x" {}
```
"""
    parser = MarkdownParser()
    blocks = parser.parse(content)
    assert len(blocks) == 1
    assert blocks[0][1].language == "hcl"
