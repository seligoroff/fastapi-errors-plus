"""DTO introspection helpers for :class:`Errors` (internal)."""

from __future__ import annotations

import copy
from typing import Any, Dict, Optional


def pick_error_dto_application_json_extra(
    error_dto: Any,
) -> Optional[Dict[str, Any]]:
    """Optional OpenAPI ``application/json`` keys from DTO (e.g. ``schema``, ``encoding``).

    Prefer ``to_openapi_json_media_type_extras()`` when present and returns a truthy mapping;
    otherwise ``schema`` field, then ``openapi_json_extras``. Must not rely on ``example`` /
    ``examples`` here — ``to_examples()`` covers those."""
    extras: Dict[str, Any] = {}
    schema = getattr(error_dto, "schema", None)
    if isinstance(schema, dict) and schema:
        extras["schema"] = schema
    attr_extra = getattr(error_dto, "openapi_json_extras", None)
    if isinstance(attr_extra, dict) and attr_extra:
        extras.update(attr_extra)
    getter = getattr(error_dto, "to_openapi_json_media_type_extras", None)
    if callable(getter):
        out = getter()
        if isinstance(out, dict) and out:
            extras.update(out)
    return extras or None


def pick_error_dto_model(error_dto: Any) -> Any:
    """Optional FastAPI ``model`` on the outer response object."""
    return getattr(error_dto, "model", None)


def collect_dto_examples(error_dto: Any) -> Dict[str, Any]:
    """Return a deep copy of examples from an ErrorDTO via ``to_examples()``."""
    cls = type(error_dto)
    has_to_examples = callable(getattr(error_dto, "to_examples", None))
    has_to_example = callable(getattr(error_dto, "to_example", None))

    if has_to_examples:
        return copy.deepcopy(error_dto.to_examples())

    if has_to_example:
        raise TypeError(
            f"{cls.__name__} implements deprecated to_example(); use to_examples() instead."
        )

    raise TypeError(f"{cls.__name__} has no to_examples() method")
