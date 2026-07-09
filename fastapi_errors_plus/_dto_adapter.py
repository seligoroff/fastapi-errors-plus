"""DTO introspection helpers for :class:`Errors` (internal)."""

from __future__ import annotations

import copy
import warnings
from typing import Any, Dict, Optional


def example_defining_class(cls: type, method: str) -> Optional[type]:
    """First class in MRO that defines *method* in its own ``__dict__``."""
    for base in cls.__mro__:
        if method in base.__dict__:
            return base
    return None


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
    """Return a deep copy of examples from an ErrorDTO.

    Resolution walks the MRO: the most specific ``to_examples`` wins over an
    inherited ``to_example`` on the same branch; legacy ``to_example`` only on
    the defining class emits a single actionable deprecation warning.
    """
    cls = type(error_dto)
    examples_cls = example_defining_class(cls, "to_examples")
    legacy_cls = example_defining_class(cls, "to_example")

    if examples_cls is not None:
        use_examples = legacy_cls is None or cls.__mro__.index(
            examples_cls
        ) <= cls.__mro__.index(legacy_cls)
        if use_examples:
            return copy.deepcopy(error_dto.to_examples())

    if legacy_cls is not None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = error_dto.to_example()
        warnings.warn(
            f"{cls.__name__} implements deprecated to_example(); use to_examples() instead.",
            DeprecationWarning,
            stacklevel=3,
        )
        return copy.deepcopy(result)

    raise TypeError(f"{cls.__name__} has no to_examples() or to_example()")
