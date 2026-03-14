"""Extract raw infrastructure requirements from parsed blocks."""

import re
from dataclasses import dataclass, field

from terraform_generator.parsing.blocks import BlockType, CodeBlock

from terraform_generator.extraction.patterns import RESOURCE_PATTERN


@dataclass
class RawRequirement:
    """Raw extracted requirement before normalization."""

    type: str
    logical_name: str
    attributes: dict = field(default_factory=dict)
    raw_content: str = ""


class Extractor:
    """Extract raw requirements from terraform/hcl code blocks."""

    HCL_LANGUAGES = ("terraform", "hcl", "tf")

    def extract(
        self, blocks: list[tuple[BlockType, object]]
    ) -> list[RawRequirement]:
        """Extract raw requirements from parsed blocks."""
        requirements: list[RawRequirement] = []

        for block_type, block in blocks:
            if block_type != BlockType.CODE_BLOCK:
                continue
            if not isinstance(block, CodeBlock):
                continue
            if block.language.lower() not in self.HCL_LANGUAGES:
                continue

            requirements.extend(self._extract_from_code_block(block.content))

        return requirements

    def _extract_from_code_block(self, content: str) -> list[RawRequirement]:
        """Extract resources from HCL code block content."""
        requirements: list[RawRequirement] = []

        for match in RESOURCE_PATTERN.finditer(content):
            resource_type = match.group(1)
            logical_name = match.group(2)
            start = match.end()
            # Find matching brace for the block
            block_content = self._extract_brace_block(content, start)
            attributes = self._parse_attributes(block_content)
            requirements.append(
                RawRequirement(
                    type=resource_type,
                    logical_name=logical_name,
                    attributes=attributes,
                    raw_content=block_content,
                )
            )

        return requirements

    def _extract_brace_block(self, content: str, start: int) -> str:
        """Extract content between matching braces."""
        depth = 1
        i = start
        while i < len(content) and depth > 0:
            if content[i] == "{":
                depth += 1
            elif content[i] == "}":
                depth -= 1
            i += 1
        return content[start : i - 1].strip()

    def _parse_attributes(self, block_content: str) -> dict:
        """Parse key = value attributes from block content."""
        attrs: dict = {}
        lines = block_content.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                i += 1
                continue

            # Simple key = value
            simple_match = re.match(r'^\s*([a-z][a-z0-9_]*)\s*=\s*(.+)$', stripped)
            if simple_match:
                key = simple_match.group(1)
                value_str = simple_match.group(2).strip()
                value = self._parse_value(value_str)
                if value is not None:
                    attrs[key] = value
                i += 1
                continue

            # Nested block: key { ... }
            block_match = re.match(r'^\s*([a-z][a-z0-9_]*)\s*\{', stripped)
            if block_match:
                key = block_match.group(1)
                # Collect lines until matching }
                nested_lines = [line]
                depth = 1
                j = i + 1
                while j < len(lines) and depth > 0:
                    for c in lines[j]:
                        if c == "{":
                            depth += 1
                        elif c == "}":
                            depth -= 1
                    nested_lines.append(lines[j])
                    j += 1
                nested_content = "\n".join(nested_lines)
                inner = self._extract_brace_block(nested_content, nested_content.index("{") + 1)
                parsed = self._parse_attributes(inner)
                # For list-like blocks (ingress, egress), use list
                if key in attrs and isinstance(attrs[key], list):
                    attrs[key].append(parsed)
                else:
                    attrs[key] = [parsed] if parsed else []
                i = j
                continue

            i += 1

        return attrs

    def _parse_value(self, value_str: str) -> str | int | bool | dict | list | None:
        """Parse a HCL-like value string."""
        value_str = value_str.strip()
        if not value_str:
            return None

        # String: "..." or "..."
        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1].replace('\\"', '"')
        if value_str.startswith("'") and value_str.endswith("'"):
            return value_str[1:-1].replace("\\'", "'")

        # Bool
        if value_str.lower() == "true":
            return True
        if value_str.lower() == "false":
            return False

        # Number
        try:
            return int(value_str)
        except ValueError:
            pass
        try:
            return float(value_str)
        except ValueError:
            pass

        # Map/object: { key = value, ... }
        if value_str.startswith("{"):
            # Simple map parsing
            inner = value_str[1:-1].strip()
            result: dict = {}
            # Naive split by comma at top level
            parts = self._split_top_level(inner, ",")
            for part in parts:
                if "=" in part:
                    k, v = part.split("=", 1)
                    result[k.strip()] = self._parse_value(v.strip())
            return result

        # Reference - keep as string for now
        return value_str

    def _split_top_level(self, s: str, sep: str) -> list[str]:
        """Split by sep only at top level (not inside braces)."""
        result: list[str] = []
        current = []
        depth = 0
        i = 0
        while i < len(s):
            if s[i] in "{[(":
                depth += 1
                current.append(s[i])
            elif s[i] in "}])":
                depth -= 1
                current.append(s[i])
            elif s[i] == sep and depth == 0:
                result.append("".join(current).strip())
                current = []
            else:
                current.append(s[i])
            i += 1
        if current:
            result.append("".join(current).strip())
        return result
