"""Extract architecture payload from validated input array."""

from terraform_generator.domain.exceptions import InputValidationError


def extract_architecture_payload(validated_list: list) -> dict:
    """
    Extract the architecture payload from the first item's 'output' field.

    The pipeline processes one architecture at a time. When the root is an array
    of items with 'output', we take the first item's output for processing.

    Raises InputValidationError if the structure is invalid.
    """
    if not validated_list:
        raise InputValidationError("Root input must be a non-empty JSON array")

    first_item = validated_list[0]
    if not isinstance(first_item, dict):
        raise InputValidationError(
            f"Each array item must be an object, got {type(first_item).__name__}"
        )

    if "output" not in first_item:
        raise InputValidationError("Each array item must contain an 'output' field")

    output = first_item["output"]
    if not isinstance(output, dict):
        raise InputValidationError(
            f"The 'output' field must be an object, got {type(output).__name__}"
        )

    return output
