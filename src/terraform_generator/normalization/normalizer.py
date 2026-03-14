"""Normalize raw requirements into domain model."""

from datetime import datetime
from pathlib import Path

from terraform_generator.domain.exceptions import NormalizationError
from terraform_generator.domain.models import (
    Architecture,
    ArchitectureMetadata,
    InfrastructureResource,
)

from terraform_generator.extraction.extractor import RawRequirement
from terraform_generator.normalization.resolver import (
    detect_cycle,
    resolve_dependencies,
    validate_dependencies,
)

V1_RESOURCE_TYPES = frozenset({
    "aws_s3_bucket",
    "aws_s3_bucket_versioning",
    "aws_instance",
    "aws_security_group",
    "aws_vpc",
    "aws_subnet",
})


class Normalizer:
    """Convert raw requirements to Architecture domain model."""

    def __init__(self, correlation_id: str, source_file: str | None = None) -> None:
        self.correlation_id = correlation_id
        self.source_file = source_file

    def normalize(
        self,
        raw_requirements: list[RawRequirement],
        name: str = "architecture",
    ) -> Architecture:
        """Build Architecture from raw requirements."""
        if not raw_requirements:
            return Architecture(
                id=self.correlation_id,
                name=name,
                provider="aws",
                resources=[],
                metadata=ArchitectureMetadata(
                    source_file=self.source_file,
                    parsed_at=datetime.utcnow(),
                    version="1.0",
                ),
            )

        # Validate resource types
        for r in raw_requirements:
            if r.type not in V1_RESOURCE_TYPES:
                raise NormalizationError(
                    f"Unsupported resource type: {r.type}. "
                    f"V1 supports: {sorted(V1_RESOURCE_TYPES)}"
                )

        # Build resources with dependencies from attributes
        resources_data: list[tuple[str, str, dict]] = [
            (r.type, r.logical_name, r.attributes) for r in raw_requirements
        ]

        deps = resolve_dependencies(resources_data)
        valid_names = {r.logical_name for r in raw_requirements}

        # Check for cycles
        cycle = detect_cycle(deps)
        if cycle:
            raise NormalizationError(f"Circular dependency detected: {' -> '.join(cycle)}")

        # Check for undefined refs
        undefined = validate_dependencies(deps, valid_names)
        if undefined:
            raise NormalizationError(
                f"Undefined dependency references: {list(dict.fromkeys(undefined))}"
            )

        # Check for duplicate logical names
        names_seen: set[str] = set()
        for r in raw_requirements:
            if r.logical_name in names_seen:
                raise NormalizationError(f"Duplicate logical_name: {r.logical_name}")
            names_seen.add(r.logical_name)

        # Build InfrastructureResource list
        resources = []
        for r in raw_requirements:
            resource_deps = deps.get(r.logical_name, [])
            resources.append(
                InfrastructureResource(
                    type=r.type,
                    logical_name=r.logical_name,
                    attributes=r.attributes,
                    dependencies=resource_deps,
                )
            )

        return Architecture(
            id=self.correlation_id,
            name=name,
            provider="aws",
            resources=resources,
            metadata=ArchitectureMetadata(
                source_file=self.source_file,
                parsed_at=datetime.utcnow(),
                version="1.0",
            ),
        )
