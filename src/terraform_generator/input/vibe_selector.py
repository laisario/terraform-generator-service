"""Select the chosen vibe from architecture payload based on user decision."""

from terraform_generator.domain.exceptions import InputValidationError

ALLOWED_DECISIONS = frozenset({"vibe_economica", "vibe_performance"})


def select_chosen_vibe(architecture_payload: dict, decision: str) -> dict:
    """
    Return a payload containing only the vibe chosen by the user.

    The returned dict has analise_entrada plus the selected vibe.
    Non-selected vibes are excluded so the analyzer processes only the chosen one.

    Raises InputValidationError if:
    - decision is not in allowed values
    - the chosen vibe does not exist or is invalid in the payload
    """
    if decision not in ALLOWED_DECISIONS:
        raise InputValidationError(
            f"Invalid decision '{decision}'. Allowed values: {sorted(ALLOWED_DECISIONS)}"
        )

    chosen_vibe = architecture_payload.get(decision)
    if not chosen_vibe or not isinstance(chosen_vibe, dict):
        raise InputValidationError(
            f"Chosen vibe '{decision}' not found or invalid in payload"
        )

    return {
        "analise_entrada": architecture_payload.get("analise_entrada", ""),
        decision: chosen_vibe,
    }
