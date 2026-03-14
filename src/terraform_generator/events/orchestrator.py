"""Synchronous pipeline orchestrator."""

import uuid
from pathlib import Path

from terraform_generator.config import Settings
from terraform_generator.domain.exceptions import (
    ExtractionError,
    GenerationError,
    IngestionError,
    NormalizationError,
    ParsingError,
    ValidationError,
)
from terraform_generator.domain.models import Architecture

from terraform_generator.events.payloads import (
    IngestRequestedPayload,
    ProcessingCompletedPayload,
    ProcessingFailedPayload,
)
from terraform_generator.extraction.extractor import Extractor
from terraform_generator.ingestion.loader import Loader
from terraform_generator.normalization.normalizer import Normalizer
from terraform_generator.parsing.markdown_parser import MarkdownParser
from terraform_generator.terraform.generator import TerraformGenerator
from terraform_generator.terraform.writer import TerraformWriter
from terraform_generator.validation.validator import Validator


class Orchestrator:
    """Orchestrate the full pipeline: ingest → parse → extract → normalize → validate → generate → output."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.loader = Loader(self.settings)
        self.parser = MarkdownParser()
        self.extractor = Extractor()
        self.validator = Validator(schema_path=self.settings.schema_path)
        self.generator = TerraformGenerator(self.settings)
        self.writer = TerraformWriter(self.settings)

    def process(
        self,
        file_path: str | Path | None = None,
        content: str | None = None,
        correlation_id: str | None = None,
    ) -> ProcessingCompletedPayload | ProcessingFailedPayload:
        """
        Process an architecture file or content.
        Returns ProcessingCompletedPayload on success, ProcessingFailedPayload on failure.
        """
        cid = correlation_id or str(uuid.uuid4())

        try:
            # 1. Ingestion
            if file_path:
                md_content = self.loader.load_from_path(file_path)
                source_file = str(file_path)
            elif content:
                md_content = self.loader.load_from_content(content)
                source_file = None
            else:
                return ProcessingFailedPayload(
                    correlation_id=cid,
                    stage="ingestion",
                    error="Either file_path or content must be provided",
                )

            # 2. Parsing
            blocks = self.parser.parse(md_content)

            # 3. Extraction
            raw_requirements = self.extractor.extract(blocks)

            # 4. Normalization
            normalizer = Normalizer(correlation_id=cid, source_file=source_file)
            architecture = normalizer.normalize(raw_requirements)

            # 5. Validation
            result = self.validator.validate(architecture)
            if not result.valid:
                errors_str = "; ".join(f"{e.code}: {e.message}" for e in result.errors)
                return ProcessingFailedPayload(
                    correlation_id=cid,
                    stage="validation",
                    error=errors_str,
                )

            # 6. Template selection + 7. Generation
            files = self.generator.generate(architecture)

            # 8. Output
            output_dir = self.settings.output_dir / cid
            self.writer.write(output_dir, files)

            return ProcessingCompletedPayload(
                correlation_id=cid,
                output_path=str(output_dir),
                summary={
                    "resources": len(architecture.resources),
                    "files": len(files),
                },
            )

        except IngestionError as e:
            return ProcessingFailedPayload(correlation_id=cid, stage="ingestion", error=str(e))
        except ParsingError as e:
            return ProcessingFailedPayload(correlation_id=cid, stage="parsing", error=str(e))
        except ExtractionError as e:
            return ProcessingFailedPayload(correlation_id=cid, stage="extraction", error=str(e))
        except NormalizationError as e:
            return ProcessingFailedPayload(correlation_id=cid, stage="normalization", error=str(e))
        except ValidationError as e:
            return ProcessingFailedPayload(correlation_id=cid, stage="validation", error=str(e))
        except GenerationError as e:
            return ProcessingFailedPayload(correlation_id=cid, stage="generation", error=str(e))
        except Exception as e:
            return ProcessingFailedPayload(
                correlation_id=cid,
                stage="unknown",
                error=f"{type(e).__name__}: {e}",
            )
