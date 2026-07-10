"""Validate ErrorDTO objects before merge (internal)."""

from __future__ import annotations

from typing import Any


def validate_error_dto(error: Any) -> None:
    """Raise if *error* does not satisfy the runtime ErrorDTO contract."""
    cls_name = type(error).__name__
    has_to_examples = callable(getattr(error, "to_examples", None))
    has_to_example = callable(getattr(error, "to_example", None))

    if has_to_example and not has_to_examples:
        raise TypeError(
            f"{cls_name} implements deprecated to_example(); use to_examples() instead."
        )

    missing_attrs = [
        attr
        for attr in ("status_code", "message")
        if not hasattr(error, attr)
    ]
    if missing_attrs or not has_to_examples:
        missing = missing_attrs + ([] if has_to_examples else ["to_examples()"])
        raise TypeError(
            f"ErrorDTO object must have status_code, message attributes "
            f"and to_examples() method. Missing: {', '.join(missing)}. "
            f"Got {cls_name}"
        )

    status_code = error.status_code
    if not isinstance(status_code, int):
        raise TypeError(
            f"{cls_name}.status_code must be int, got {type(status_code).__name__}"
        )
    if not 100 <= status_code <= 599:
        raise ValueError(
            f"{cls_name}.status_code must be between 100 and 599, got {status_code}"
        )

    message = error.message
    if not isinstance(message, str) or not message.strip():
        raise ValueError(
            f"{cls_name}.message must be a non-empty str, got {message!r}"
        )

    examples = error.to_examples()
    if not isinstance(examples, dict):
        raise TypeError(
            f"{cls_name}.to_examples() must return dict, got {type(examples).__name__}"
        )
