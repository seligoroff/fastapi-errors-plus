"""Declarative error documentation for OpenAPI."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from fastapi_errors_plus.example_utils import ExampleSpec, _normalize_example_specs


@dataclass
class ErrorDoc:
    """Declarative ErrorDTO with arbitrary example bodies and optional summaries.

    ``examples`` values:

    * **str** — shorthand ``{"detail": text}`` (same as bundled DTOs).
    * **dict** with only OpenAPI Example Object keys (``value``, ``summary``, …) —
      used as the Example Object.
    * **any other dict** — treated as the full response **body** (e.g.
      ``{"code": "...", "detail": "...", "value": 150}``).

    Example:
        ```python
        ErrorDoc(
            status_code=403,
            message="Insufficient permissions",
            examples={
                "MissingRole": {
                    "summary": "User lacks required role",
                    "value": {"code": "FORBIDDEN", "detail": "Role admin required"},
                },
            },
        )
        ```
    """

    status_code: int
    message: str
    examples: Optional[Dict[str, ExampleSpec]] = None
    body: Optional[Dict[str, Any]] = None
    example_key: Optional[str] = None
    model: Any = field(default=None, repr=False)
    """Optional Pydantic model for FastAPI ``responses`` (outer ``model=`` key)."""

    schema: Optional[Dict[str, Any]] = field(default=None, repr=False)
    """Optional JSON Schema under ``content['application/json']['schema']``."""

    openapi_json_extras: Optional[Dict[str, Any]] = field(default=None)

    def to_examples(self) -> Dict[str, Any]:
        """Build OpenAPI ``examples`` map for ``application/json``."""
        if self.examples is not None:
            return _normalize_example_specs(self.examples)
        key = self.example_key or self.message
        value = self.body if self.body is not None else {"detail": self.message}
        return {key: {"value": value}}

