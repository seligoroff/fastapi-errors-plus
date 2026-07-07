"""Protocol for error DTOs compatible with fastapi-errors-plus."""

from typing import Any, Dict, Protocol, Union, runtime_checkable


@runtime_checkable
class ErrorDTO(Protocol):
    """Target interface for error objects used with :class:`Errors`.

      Implement ``to_examples()`` returning an OpenAPI ``examples`` map::

          {"ExampleKey": {"value": {...}, "summary": "..."}}

    Legacy classes that only define ``to_example()`` are accepted at **runtime**
    by :class:`Errors` but do **not** satisfy this protocol for static typing.
    See :class:`LegacyErrorDTO`.
    """

    status_code: int
    message: str

    def to_examples(self) -> Dict[str, Any]:
        """Generate OpenAPI ``examples`` for this error."""
        ...


@runtime_checkable
class LegacyErrorDTO(Protocol):
    """Deprecated: only ``to_example()`` — migrate to :class:`ErrorDTO`."""

    status_code: int
    message: str

    def to_example(self) -> Dict[str, Any]:
        """Deprecated OpenAPI ``examples`` map."""
        ...


# Annotation helper for codebases still on legacy ``to_example()`` only.
ErrorDTOLike = Union[ErrorDTO, LegacyErrorDTO]
