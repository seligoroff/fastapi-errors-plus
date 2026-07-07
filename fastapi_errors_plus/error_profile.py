"""Project-wide defaults for :class:`Errors` (release 0.9)."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ErrorProfile:
    """Immutable project defaults applied before per-endpoint ``Errors(...)`` args.

    Explicit ``Errors`` keyword flags override profile values. Positional dict/DTO
    errors are merged after profile-driven standard statuses.

    Example:
        ```python
        ADR = ErrorProfile(
            validation_error_422=False,
            unauthorized_401=True,
            internal_server_error_500=True,
        )

        @router.post("/items", responses=Errors(business_conflict, profile=ADR))
        def create_item():
            ...
        ```
    """

    unauthorized_401: bool = False
    forbidden_403: bool = False
    validation_error_422: Optional[bool] = None
    internal_server_error_500: bool = False
