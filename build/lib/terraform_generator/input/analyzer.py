"""Analyze JSON recursos and map to raw requirements for normalization."""

import re
from collections import defaultdict

from terraform_generator.domain.exceptions import InputValidationError
from terraform_generator.domain.models import RawRequirement

V1_RESOURCE_TYPES = frozenset({
    "aws_s3_bucket",
    "aws_s3_bucket_versioning",
    "aws_instance",
    "aws_security_group",
    "aws_vpc",
    "aws_subnet",
})


def _sanitize_logical_name(name: str) -> str:
    """Convert to valid logical_name: lowercase, alphanumeric + underscore."""
    s = re.sub(r"[^a-z0-9_]", "_", name.lower())
    s = re.sub(r"_+", "_", s).strip("_")
    if not s or not s[0].isalpha():
        s = "r" + s
    return s or "resource"


def _derive_logical_name(servico: str, config: dict | str, type_counters: dict[str, int]) -> str:
    """Derive logical_name from servico and config."""
    short_type = servico.replace("aws_", "") if servico.startswith("aws_") else servico
    idx = type_counters[short_type]
    type_counters[short_type] += 1

    # Prefer config-based names when available
    if isinstance(config, dict):
        if servico == "aws_s3_bucket" and "bucket" in config:
            base = _sanitize_logical_name(str(config["bucket"]))
            return f"{base}_bucket" if base else f"s3_bucket_{idx}"
        if servico == "aws_security_group" and "name" in config:
            base = _sanitize_logical_name(str(config["name"]))
            return f"{base}_sg" if base else f"security_group_{idx}"
        if servico == "aws_instance" and config.get("tags", {}).get("Role"):
            base = _sanitize_logical_name(str(config["tags"]["Role"]))
            return f"{base}_{idx}" if base else f"instance_{idx}"

    return f"{short_type}_{idx}"


class InputAnalyzer:
    """Analyze vibe_economica and vibe_performance recursos into RawRequirement list."""

    def analyze(self, data: dict) -> list[RawRequirement]:
        """
        Extract resources from vibe_economica and vibe_performance.
        Uses vibe_economica first, then vibe_performance (merge).
        Raises InputValidationError for unsupported services.
        """
        requirements: list[RawRequirement] = []
        type_counters: dict[str, int] = defaultdict(int)

        for vibe_key in ("vibe_economica", "vibe_performance"):
            vibe = data.get(vibe_key)
            if not vibe or not isinstance(vibe, dict):
                continue
            recursos = vibe.get("recursos")
            if not isinstance(recursos, list):
                continue

            for recurso in recursos:
                if not isinstance(recurso, dict):
                    continue
                servico = recurso.get("servico")
                if not servico or not isinstance(servico, str):
                    continue

                servico = servico.strip()
                if servico not in V1_RESOURCE_TYPES:
                    raise InputValidationError(
                        f"Unsupported service '{servico}'. "
                        f"V1 supports: {sorted(V1_RESOURCE_TYPES)}"
                    )

                config = recurso.get("config")
                if config is None:
                    config = {}
                elif isinstance(config, str):
                    config = {"raw": config}
                elif not isinstance(config, dict):
                    config = {"raw": str(config)}

                logical_name = _derive_logical_name(servico, config, type_counters)
                requirements.append(
                    RawRequirement(
                        type=servico,
                        logical_name=logical_name,
                        attributes=dict(config),
                        raw_content="",
                    )
                )

        return requirements
