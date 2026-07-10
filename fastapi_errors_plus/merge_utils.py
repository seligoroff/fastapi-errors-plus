"""Shared OpenAPI example merge helpers (internal)."""

import copy
import warnings
from typing import Any, Callable, Dict, Optional

# Example keys produced by standard HTTP status flags in :class:`Errors`.
STANDARD_FLAG_EXAMPLE_KEYS: Dict[int, str] = {
    401: "StandardUnauthorized",
    403: "StandardForbidden",
    422: "StandardValidationError",
    500: "StandardInternalServerError",
}

# OpenAPI Media Type: merge example/examples separately; other keys win from extras.
OPENAPI_MEDIA_TYPE_EXAMPLE_KEYS = frozenset({"example", "examples"})


def unique_key(examples: Dict[str, Any], base: str) -> str:
    """Return a key not present in *examples*, using ``{base}_2``, ``{base}_3``, …"""
    key = base
    i = 2
    while key in examples:
        key = f"{base}_{i}"
        i += 1
    return key


def merge_openapi_application_json_non_example(
    existing_json: Dict[str, Any],
    response_json: Dict[str, Any],
) -> None:
    """Apply schema/encoding/extra fields from incoming media type; incoming overwrites on conflict."""
    for key, value in response_json.items():
        if key not in OPENAPI_MEDIA_TYPE_EXAMPLE_KEYS:
            existing_json[key] = value


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
        warnings.warn(
            "content['application/json']['examples'] must be a dict, "
            f"got {type(existing).__name__}; resetting to an empty dict.",
            UserWarning,
            stacklevel=3,
        )
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
    unique_key_fn: Optional[Callable[[Dict[str, Any], str], str]] = None,
) -> None:
    """Merge an ``examples`` map into ``media_json``.

    Policy:
    - if an incoming example key collides with an existing one, do NOT silently
      overwrite; instead, allocate a unique key (when ``unique_key_fn`` is provided).
    - if no ``unique_key_fn`` is provided, fall back to last-wins overwrite
      (backwards compatible behavior for any internal callers).
    """
    examples = ensure_examples_dict(media_json, prior_singular_key=prior_singular_key)
    for key, value in incoming_examples.items():
        if key in examples and examples[key] == value:
            continue
        if key not in examples:
            examples[key] = copy.deepcopy(value)
            continue
        if unique_key_fn is None:
            # Backwards compatible fallback: silent overwrite.
            examples[key] = copy.deepcopy(value)
            continue
        resolved_key = unique_key_fn(examples, key)
        examples[resolved_key] = copy.deepcopy(value)

