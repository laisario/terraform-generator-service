"""Regex and pattern definitions for HCL extraction."""

import re

# resource "aws_s3_bucket" "main_bucket" { ... }
RESOURCE_PATTERN = re.compile(
    r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{',
    re.MULTILINE,
)

# Reference: aws_security_group.web_sg.id or aws_security_group.web_sg
REFERENCE_PATTERN = re.compile(
    r'([a-z][a-z0-9_]*)\s*\.\s*([a-z][a-z0-9_]*)',
)

# Simple key = value (string, number, or reference)
# Handles: key = "value", key = 123, key = var.x
ATTR_SIMPLE = re.compile(
    r'^\s*([a-z][a-z0-9_]*)\s*=\s*(.+?)(?:\s*#|$)',
    re.MULTILINE,
)

# Nested block: key { ... } - we need to parse the inner content
BLOCK_OPEN = re.compile(r'^\s*([a-z][a-z0-9_]*)\s*\{', re.MULTILINE)
