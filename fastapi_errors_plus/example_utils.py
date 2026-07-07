"""OpenAPI example normalization shared by ErrorDoc and bundled DTOs."""

import warnings
from typing import Any, Dict, Union

# OpenAPI 3 Example Object allowed keys (subset used by this library).
_OPENAPI_EXAMPLE_OBJECT_KEYS = frozenset(
    {"value", "summary", "description", "externalValue"}
)

ExampleSpec = Union[str, Dict[str, Any]]


def _is_openapi_example_object(spec: Dict[str, Any]) -> bool:
    """True if *spec* looks like an OpenAPI Example Object, not a response body."""
    if not spec:
        return False
    return set(spec.keys()) <= _OPENAPI_EXAMPLE_OBJECT_KEYS


def _normalize_example_specs(specs: Dict[str, ExampleSpec]) -> Dict[str, Any]:
    """Normalize user specs to OpenAPI ``examples`` map.

    * ``str`` — shorthand for ``{"value": {"detail": str}}`` (legacy detail shape).
    * ``dict`` — if keys are only OpenAPI Example Object fields, used as-is;
      otherwise the whole dict is treated as the response **body** wrapped in
      ``{"value": body}`` (avoids mis-parsing bodies that contain a ``value`` field).
    """
    out: Dict[str, Any] = {}
    for key, spec in specs.items():
        if isinstance(spec, str):
            out[key] = {"value": {"detail": spec}}
        elif isinstance(spec, dict):
            if _is_openapi_example_object(spec):
                out[key] = dict(spec)
            else:
                extra = set(spec.keys()) - _OPENAPI_EXAMPLE_OBJECT_KEYS
                if "value" in spec and extra:
                    warnings.warn(
                        f"Example {key!r}: keys {sorted(extra)} look like a response body, "
                        "not an OpenAPI Example Object; wrapping the dict as the example value. "
                        "Use explicit Example Object keys only "
                        "(value, summary, description, externalValue) at the top level.",
                        UserWarning,
                        stacklevel=3,
                    )
                out[key] = {"value": spec}
        else:
            raise TypeError(
                f"Example spec for key {key!r} must be str or dict, got {type(spec).__name__}"
            )
    return out
