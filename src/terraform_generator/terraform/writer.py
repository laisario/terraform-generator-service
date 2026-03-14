"""Write Terraform files to disk."""

from pathlib import Path

from terraform_generator.config import Settings


class TerraformWriter:
    """Write generated Terraform files to output directory."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()

    def write(
        self,
        output_dir: Path,
        files: list[tuple[str, str]],
    ) -> Path:
        """
        Write Terraform files to output_dir.
        Returns the output directory path.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for filename, content in files:
            file_path = output_dir / filename
            file_path.write_text(content, encoding="utf-8")

        return output_dir
