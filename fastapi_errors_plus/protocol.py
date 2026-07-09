"""Protocol for error DTOs compatible with fastapi-errors-plus."""

from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class ErrorDTO(Protocol):
    """Target interface for error objects used with :class:`Errors`.

    Implement ``to_examples()`` returning an OpenAPI ``examples`` map::

        {"ExampleKey": {"value": {...}, "summary": "..."}}
    """

    status_code: int
    message: str

    def to_examples(self) -> Dict[str, Any]:
        """Generate OpenAPI ``examples`` for this error."""
        ...
