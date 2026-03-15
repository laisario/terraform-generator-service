"""Entry point for Terraform Generator Service."""

import argparse
import sys
from pathlib import Path

from terraform_generator.config import Settings
from terraform_generator.events.orchestrator import Orchestrator
from terraform_generator.events.payloads import (
    ProcessingCompletedPayload,
    ProcessingFailedPayload,
)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Process JSON infrastructure definitions and generate Terraform files"
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to JSON input file",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="output",
        help="Output directory for generated Terraform files (default: output)",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read JSON from stdin instead of file",
    )
    args = parser.parse_args()

    if args.stdin:
        content = sys.stdin.read()
        file_path = None
    elif args.input:
        file_path = args.input
        content = None
    else:
        parser.error("Provide an input file path or use --stdin")

    settings = Settings(output_dir=Path(args.output_dir))
    orchestrator = Orchestrator(settings=settings)

    result = orchestrator.process(file_path=file_path, content=content)

    if isinstance(result, ProcessingCompletedPayload):
        print(f"Success: Terraform files written to {result.output_path}")
        print(f"  Resources: {result.summary.get('resources', 0)}")
        print(f"  Files: {result.summary.get('files', 0)}")
        sys.exit(0)
    else:
        assert isinstance(result, ProcessingFailedPayload)
        print(f"Error [{result.stage}]: {result.error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
