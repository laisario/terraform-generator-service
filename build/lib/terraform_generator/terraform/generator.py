"""Render Terraform files from Jinja2 templates."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from terraform_generator.config import Settings
from terraform_generator.domain.models import Architecture

from terraform_generator.terraform.template_selector import TemplateMapping, TemplateSelector


def _resolve_templates_dir(settings: Settings) -> Path:
    """Resolve templates directory (relative to project root or cwd)."""
    base = Path(__file__).resolve().parent.parent.parent.parent
    path = base / settings.templates_dir
    if path.exists():
        return path
    return Path(settings.templates_dir)


class TerraformGenerator:
    """Generate Terraform content from templates."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.selector = TemplateSelector()
        templates_path = _resolve_templates_dir(self.settings)
        self._env = Environment(
            loader=FileSystemLoader(templates_path),
            autoescape=select_autoescape(default=False),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(
        self,
        architecture: Architecture,
        provider_config: dict | None = None,
    ) -> list[tuple[str, str]]:
        """
        Generate Terraform file contents.
        Returns list of (filename, content) tuples.
        """
        provider_config = provider_config or {"region": "us-east-1"}
        mappings = self.selector.select(architecture)

        files: list[tuple[str, str]] = []

        # main.tf
        main_template = self._env.get_template("main.tf.j2")
        main_content = main_template.render(provider_config=provider_config)
        files.append(("main.tf", main_content))

        for mapping in mappings:
            template = self._env.get_template(mapping.template_name)
            content = template.render(
                resources=mapping.resources,
                provider_config=provider_config,
            )
            if content.strip():
                files.append((mapping.output_file, content))

        return files
