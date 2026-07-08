"""Shared OpenAPI example merge helpers (internal)."""

from typing import Any, Callable, Dict, Optional

# Example keys produced by standard HTTP status flags in :class:`Errors`.
STANDARD_FLAG_EXAMPLE_KEYS: Dict[int, str] = {
    401: "StandardUnauthorized",
    403: "StandardForbidden",
    422: "StandardValidationError",
    500: "StandardInternalServerError",
}


def standard_flag_example_key(status_code: int) -> str:
    """Return the examples-map key for a standard flag on *status_code*."""
    return STANDARD_FLAG_EXAMPLE_KEYS.get(status_code, f"Standard{status_code}")


def ensure_examples_dict(
    media_json: Dict[str, Any],
    *,
    prior_singular_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Ensure ``media_json`` has an ``examples`` dict; promote singular ``example`` if needed."""
    if "examples" in media_json:
        existing = media_json["examples"]
        if isinstance(existing, dict):
            return existing
        # Defensive fallback for malformed user dicts.
        fallback: Dict[str, Any] = {}
        media_json["examples"] = fallback
        return fallback
    examples: Dict[str, Any] = {}
    if "example" in media_json:
        key = prior_singular_key or "default"
        examples[key] = {"value": media_json.pop("example")}
    media_json["examples"] = examples
    return examples


def merge_singular_example(
    media_json: Dict[str, Any],
    example_body: Dict[str, Any],
    *,
    prior_singular_key: Optional[str] = None,
    incoming_key: Optional[str] = None,
    unique_key_fn: Callable[[Dict[str, Any], str], str],
) -> None:
    """Merge one OpenAPI ``example`` body into ``media_json`` as part of ``examples``."""
    examples = ensure_examples_dict(media_json, prior_singular_key=prior_singular_key)
    target_key = incoming_key or "default"
    if target_key not in examples:
        examples[target_key] = {"value": example_body}
    else:
        unique = unique_key_fn(examples, "CustomExample")
        examples[unique] = {"value": example_body}


def merge_examples_map(
    media_json: Dict[str, Any],
    incoming_examples: Dict[str, Any],
    *,
    prior_singular_key: Optional[str] = None,
) -> None:
    """Merge an ``examples`` map into ``media_json``."""
    examples = ensure_examples_dict(media_json, prior_singular_key=prior_singular_key)
    examples.update(incoming_examples)
