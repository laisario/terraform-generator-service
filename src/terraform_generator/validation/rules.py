"""Custom validation rules."""

from dataclasses import dataclass


@dataclass
class ValidationIssue:
    """A single validation error or warning."""

    code: str
    message: str
    path: str | None = None


REQUIRED_ATTRIBUTES: dict[str, list[str]] = {
    "aws_s3_bucket": ["bucket"],
    "aws_s3_bucket_versioning": ["bucket"],
    "aws_instance": ["ami", "instance_type"],
    "aws_security_group": ["name", "description"],
    "aws_vpc": ["cidr_block"],
    "aws_subnet": ["vpc_id", "cidr_block", "availability_zone"],
}


def check_required_attributes(resource_type: str, attributes: dict) -> list[ValidationIssue]:
    """Check that required attributes are present."""
    issues: list[ValidationIssue] = []
    required = REQUIRED_ATTRIBUTES.get(resource_type, [])
    for attr in required:
        if attr not in attributes or attributes[attr] is None:
            issues.append(
                ValidationIssue(
                    code="missing_required_attribute",
                    message=f"Resource type {resource_type} requires attribute '{attr}'",
                    path=f"resources[].attributes.{attr}",
                )
            )
    return issues


def check_empty_resources(resources: list) -> list[ValidationIssue]:
    """Warn if no resources defined."""
    if not resources:
        return [
            ValidationIssue(
                code="empty_resources",
                message="No resources defined in architecture",
                path="resources",
            )
        ]
    return []
