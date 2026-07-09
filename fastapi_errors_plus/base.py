"""Base implementations of ErrorDTO protocol for convenience."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from fastapi_errors_plus.example_utils import ExampleSpec, _normalize_example_specs


@dataclass
class BaseErrorDTO:
    """Base implementation of ErrorDTO Protocol.

    Projects can use this class directly or create their own implementation
    that implements ErrorDTO Protocol through structural typing.

    This class provides a simple way to create error DTOs without writing
    boilerplate code in every project.

    Example:
        ```python
        from fastapi_errors_plus import Errors, BaseErrorDTO

        notification_error = BaseErrorDTO(
            status_code=404,
            message="Notification not found",
        )

        @router.delete(
            "/{id}",
            responses=Errors(notification_error),
        )
        def delete_item(id: int):
            pass
        ```
    """

    status_code: int
    """HTTP status code for the error."""

    message: str
    """Error message description."""

    model: Any = field(default=None, repr=False)
    """Optional Pydantic model for FastAPI ``responses`` (outer ``model=`` key)."""

    schema: Optional[Dict[str, Any]] = field(default=None, repr=False)
    """Optional JSON Schema under ``content['application/json']['schema']``."""

    openapi_json_extras: Optional[Dict[str, Any]] = field(default=None)
    """Optional OpenAPI fragment under ``content['application/json']`` besides examples,
    typically ``{\"schema\": ...}`` or ``encoding``. Do **not** put ``example`` / ``examples``
    here — use :meth:`to_examples`. Arbitrary implementations may instead implement
    :meth:`to_openapi_json_media_type_extras`; that return value wins over this attribute."""

    def to_examples(self) -> Dict[str, Any]:
        """Generate OpenAPI ``examples`` for this error."""
        return {
            self.message: {
                "value": {"detail": self.message},
            },
        }

@dataclass
class StandardErrorDTO(BaseErrorDTO):
    """Extended implementation for errors with multiple examples.

    Useful for standard HTTP errors (401, 403) that can have different
    causes with different messages.

    Example:
        ```python
        from fastapi_errors_plus import Errors, StandardErrorDTO

        unauthorized_error = StandardErrorDTO(
            status_code=401,
            message="Unauthorized",
            examples={
                "InvalidToken": "Ошибка декодирования токена.",
                "SessionNotFound": "Сессия пользователя не была найдена.",
            },
        )

        @router.delete(
            "/{id}",
            responses=Errors(unauthorized_error),
        )
        def delete_item(id: int):
            pass
        ```
    """

    examples: Optional[Dict[str, ExampleSpec]] = field(default=None)
    """Examples: ``str`` detail text or full OpenAPI example object (with ``summary``)."""

    def __post_init__(self) -> None:
        """Initialize examples with default value if not provided."""
        if self.examples is None:
            self.examples = {self.message: self.message}

    def to_examples(self) -> Dict[str, Any]:
        """Generate OpenAPI ``examples`` with optional summaries."""
        assert self.examples is not None
        return _normalize_example_specs(self.examples)

