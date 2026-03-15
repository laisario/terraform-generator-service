"""Dependency resolution and cycle detection."""

import re
from collections import defaultdict

from terraform_generator.domain.exceptions import NormalizationError


def extract_references_from_attributes(attributes: dict) -> list[str]:
    """Extract logical_name references from attributes (e.g., aws_security_group.web_sg)."""
    refs: list[str] = []
    ref_pattern = re.compile(r"([a-z][a-z0-9_]*)\s*\.\s*([a-z][a-z0-9_]*)(?:\s*\.\s*[a-z0-9_]+)?")

    def scan(obj: object) -> None:
        if isinstance(obj, str):
            for m in ref_pattern.finditer(obj):
                prefix = m.group(1)
                if prefix.startswith("aws_"):
                    refs.append(m.group(2))  # logical_name part
        elif isinstance(obj, dict):
            for v in obj.values():
                scan(v)
        elif isinstance(obj, list):
            for item in obj:
                scan(item)

    scan(attributes)
    return refs


def resolve_dependencies(
    resources: list[tuple[str, str, dict]]
) -> dict[str, list[str]]:
    """
    Build dependency map: logical_name -> list of logical_names it depends on.
    Returns dict mapping each logical_name to its dependencies.
    """
    name_to_attrs: dict[str, dict] = {}
    for _, logical_name, attrs in resources:
        name_to_attrs[logical_name] = attrs

    deps: dict[str, list[str]] = {}
    for logical_name, attrs in name_to_attrs.items():
        refs = extract_references_from_attributes(attrs)
        deps[logical_name] = list(dict.fromkeys(refs))  # dedupe, preserve order

    return deps


def detect_cycle(dependencies: dict[str, list[str]]) -> list[str] | None:
    """
    Detect cycle in dependency graph using DFS.
    Returns the cycle as list of logical_names if found, else None.
    """
    visited: set[str] = set()
    rec_stack: set[str] = set()
    path: list[str] = []
    cycle_path: list[str] = []

    def dfs(node: str) -> bool:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for dep in dependencies.get(node, []):
            if dep not in visited:
                if dfs(dep):
                    return True
            elif dep in rec_stack:
                # Cycle found
                idx = path.index(dep)
                cycle_path.extend(path[idx:] + [dep])
                return True

        path.pop()
        rec_stack.discard(node)
        return False

    for node in dependencies:
        if node not in visited and dfs(node):
            return cycle_path

    return None


def validate_dependencies(
    dependencies: dict[str, list[str]], valid_names: set[str]
) -> list[str]:
    """Check for undefined dependencies. Returns list of undefined refs."""
    undefined: list[str] = []
    for deps in dependencies.values():
        for d in deps:
            if d not in valid_names:
                undefined.append(d)
    return undefined
