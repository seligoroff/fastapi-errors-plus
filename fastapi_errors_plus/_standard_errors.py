"""Standard HTTP error bodies and OpenAPI fragments for library-managed flags."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

# Example body aligned with FastAPI ``HTTPValidationError`` (``detail`` is an array).
STANDARD_VALIDATION_ERROR_EXAMPLE: Dict[str, Any] = {
    "detail": [
        {
            "type": "missing",
            "loc": ["body", "field"],
            "msg": "Field required",
            "input": {},
        }
    ]
}

# Inline fallbacks when ``fastapi.openapi.utils`` definitions are unavailable.
_FALLBACK_VALIDATION_ERROR_SCHEMA: Dict[str, Any] = {
    "title": "ValidationError",
    "type": "object",
    "required": ["loc", "msg", "type"],
    "properties": {
        "loc": {
            "title": "Location",
            "type": "array",
            "items": {
                "anyOf": [{"type": "string"}, {"type": "integer"}],
            },
        },
        "msg": {"title": "Message", "type": "string"},
        "type": {"title": "Error Type", "type": "string"},
        "input": {"title": "Input"},
        "ctx": {"title": "Context", "type": "object"},
    },
}

_FALLBACK_HTTP_VALIDATION_ERROR_SCHEMA: Dict[str, Any] = {
    "title": "HTTPValidationError",
    "type": "object",
    "properties": {
        "detail": {
            "title": "Detail",
            "type": "array",
            "items": deepcopy(_FALLBACK_VALIDATION_ERROR_SCHEMA),
        },
    },
}


def standard_validation_error_example() -> Dict[str, Any]:
    """Return a copy of the library-managed 422 example body."""
    return deepcopy(STANDARD_VALIDATION_ERROR_EXAMPLE)


def standard_validation_error_openapi_json_extras() -> Dict[str, Any]:
    """Return ``application/json`` extras (``schema``) for the standard 422 flag."""
    try:
        from fastapi.openapi.utils import validation_error_response_definition

        return {"schema": deepcopy(validation_error_response_definition)}
    except ImportError:
        return {"schema": deepcopy(_FALLBACK_HTTP_VALIDATION_ERROR_SCHEMA)}
