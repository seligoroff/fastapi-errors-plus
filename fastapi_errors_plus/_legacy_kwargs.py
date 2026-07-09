"""Reject removed legacy ``Errors`` keyword arguments (1.0)."""

from __future__ import annotations

from typing import Any

_LEGACY_ERRORS_KWARGS: dict[str, str] = {
    "unauthorized": "unauthorized_401",
    "forbidden": "forbidden_403",
    "validation_error": "validation_error_422",
    "internal_server_error": "internal_server_error_500",
}


def reject_legacy_errors_kwargs(kwargs: dict[str, Any]) -> None:
    """Raise ``TypeError`` for kwargs removed in 1.0."""
    for key, replacement in _LEGACY_ERRORS_KWARGS.items():
        if key in kwargs:
            raise TypeError(
                f"{key!r} was removed; use {replacement!r} instead."
            )
    if kwargs:
        unknown = next(iter(kwargs))
        raise TypeError(f"unexpected keyword argument {unknown!r}")
