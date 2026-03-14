"""Block types for parsed Markdown structure."""

from enum import Enum
from typing import Union

from pydantic import BaseModel


class BlockType(str, Enum):
    """Type of parsed block."""

    HEADING = "heading"
    CODE_BLOCK = "code_block"
    LIST = "list"


class Heading(BaseModel):
    """Heading block with level and text."""

    level: int
    text: str


class CodeBlock(BaseModel):
    """Code block with language and content."""

    language: str = ""
    content: str


Block = Union[Heading, CodeBlock]
