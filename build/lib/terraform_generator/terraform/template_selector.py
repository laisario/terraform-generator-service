"""Map domain resources to template files."""

from collections import defaultdict
from dataclasses import dataclass

from terraform_generator.domain.models import Architecture, InfrastructureResource


@dataclass
class TemplateMapping:
    """Mapping of resource type to output file and resources."""

    output_file: str
    template_name: str
    resources: list[InfrastructureResource]


# Resource type -> (output file name, template file name)
TYPE_TO_TEMPLATE: dict[str, tuple[str, str]] = {
    "aws_s3_bucket": ("s3_buckets.tf", "aws_s3_bucket.tf.j2"),
    "aws_s3_bucket_versioning": ("s3_bucket_versioning.tf", "aws_s3_bucket_versioning.tf.j2"),
    "aws_instance": ("instances.tf", "aws_instance.tf.j2"),
    "aws_security_group": ("security_groups.tf", "aws_security_group.tf.j2"),
    "aws_vpc": ("vpcs.tf", "aws_vpc.tf.j2"),
    "aws_subnet": ("subnets.tf", "aws_subnet.tf.j2"),
}


class TemplateSelector:
    """Select templates for architecture resources."""

    def select(self, architecture: Architecture) -> list[TemplateMapping]:
        """Group resources by type and return template mappings."""
        by_type: dict[str, list[InfrastructureResource]] = defaultdict(list)
        for resource in architecture.resources:
            by_type[resource.type].append(resource)

        mappings: list[TemplateMapping] = []
        for resource_type, resources in sorted(by_type.items()):
            if resource_type in TYPE_TO_TEMPLATE:
                output_file, template_name = TYPE_TO_TEMPLATE[resource_type]
                mappings.append(
                    TemplateMapping(
                        output_file=output_file,
                        template_name=template_name,
                        resources=resources,
                    )
                )

        return mappings
