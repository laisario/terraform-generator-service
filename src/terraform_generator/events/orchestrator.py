"""Synchronous pipeline orchestrator."""

import uuid
from pathlib import Path

from terraform_generator.config import Settings
from terraform_generator.domain.exceptions import (
    GenerationError,
    IngestionError,
    InputValidationError,
    NormalizationError,
    ValidationError,
)
from terraform_generator.domain.models import Architecture

from terraform_generator.events.payloads import (
    ProcessingCompletedPayload,
    ProcessingFailedPayload,
)
from terraform_generator.ingestion.loader import Loader
from terraform_generator.input.analyzer import InputAnalyzer
from terraform_generator.input.validator import InputValidator
from terraform_generator.normalization.normalizer import Normalizer
from terraform_generator.storage.handler import StorageHandler
from terraform_generator.terraform.generator import TerraformGenerator
from terraform_generator.validation.validator import Validator


class Orchestrator:
    """Orchestrate the full pipeline: ingest → validate JSON → analyze → normalize → validate → generate → output."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.loader = Loader(self.settings)
        self.input_validator = InputValidator(settings=self.settings)
        self.analyzer = InputAnalyzer()
        self.validator = Validator(schema_path=self.settings.schema_path)
        self.generator = TerraformGenerator(self.settings)
        self.storage_handler = StorageHandler(self.settings)

    def process(
        self,
        file_path: str | Path | None = None,
        content: str | None = None,
        correlation_id: str | None = None,
    ) -> ProcessingCompletedPayload | ProcessingFailedPayload:
        """
        Process a JSON input file or content.
        Returns ProcessingCompletedPayload on success, ProcessingFailedPayload on failure.
        """
        cid = correlation_id or str(uuid.uuid4())

        try:
            # 1. Ingestion
            if file_path:
                data = self.loader.load_from_path(file_path)
                source_file = str(file_path)
            elif content:
                data = self.loader.load_from_content(content)
                source_file = None
            else:
                return ProcessingFailedPayload(
                    correlation_id=cid,
                    stage="ingestion",
                    error="Either file_path or content must be provided",
                )

            # 2. JSON validation
            self.input_validator.validate(data)

            # 3. Service analysis
            raw_requirements = self.analyzer.analyze(data)

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

            # 8. Persistence: dev=local only, production=S3 only (no local write)
            success, object_keys = self.storage_handler.persist(files, cid)
            if not success:
                partial = object_keys if object_keys is not None else []
                return ProcessingFailedPayload(
                    correlation_id=cid,
                    stage="artifact_upload",
                    error="Artifact upload to object storage failed",
                    partial_uploads=partial,
                )

            summary = {
                "resources": len(architecture.resources),
                "files": len(files),
            }
            if object_keys:
                summary["object_keys"] = object_keys

            # output_path: local dir in dev, S3 virtual path in production
            env = self.settings.environment.lower()
            if env == "dev":
                output_path = str(self.settings.output_dir / cid)
            else:
                output_path = f"s3://{self.settings.storage_bucket}/output/{cid}/"

            return ProcessingCompletedPayload(
                correlation_id=cid,
                output_path=output_path,
                summary=summary,
            )

        except IngestionError as e:
            return ProcessingFailedPayload(correlation_id=cid, stage="ingestion", error=str(e))
        except InputValidationError as e:
            return ProcessingFailedPayload(correlation_id=cid, stage="input_validation", error=str(e))
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
