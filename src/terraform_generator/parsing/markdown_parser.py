"""Parse Markdown into structured blocks."""

from markdown_it import MarkdownIt
from markdown_it.token import Token

from terraform_generator.parsing.blocks import BlockType, CodeBlock, Heading


class MarkdownParser:
    """Parse Markdown text into a list of blocks (headings, code blocks)."""

    def __init__(self) -> None:
        self._md = MarkdownIt()

    def parse(self, content: str) -> list[tuple[BlockType, Heading | CodeBlock]]:
        """Parse Markdown content into a list of (BlockType, block) tuples."""
        tokens = self._md.parse(content)
        blocks: list[tuple[BlockType, Heading | CodeBlock]] = []

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token.type == "heading_open":
                level = int(token.tag[1])  # h1 -> 1, h2 -> 2
                # Next token is inline with the text
                if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
                    text = tokens[i + 1].content
                else:
                    text = ""
                blocks.append((BlockType.HEADING, Heading(level=level, text=text)))
                i += 2  # Skip heading_open and inline
                continue

            if token.type == "fence":
                lang = token.info.strip().lower() if token.info else ""
                blocks.append(
                    (BlockType.CODE_BLOCK, CodeBlock(language=lang, content=token.content))
                )

            i += 1

        return blocks
