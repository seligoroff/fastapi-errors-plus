"""Main Errors class for documenting errors in FastAPI endpoints."""

import copy
from collections.abc import Mapping
from typing import Any, Dict, Iterator, Optional, Union

from fastapi import status

from fastapi_errors_plus._compat import HTTP_422 as _HTTP_422
from fastapi_errors_plus._descriptions import (
    STANDARD_DESCRIPTIONS as _STANDARD_DESCRIPTIONS,
    ensure_response_descriptions,
)
from fastapi_errors_plus._flags_and_profile import resolve_standard_flags
from fastapi_errors_plus._merge_engine import (
    MergeState,
    add_dict_error,
    add_error_dto,
    add_standard_error,
)
from fastapi_errors_plus.error_profile import ErrorProfile
from fastapi_errors_plus.merge_utils import unique_key
from fastapi_errors_plus.protocol import ErrorDTO, LegacyErrorDTO


class Errors(Mapping):
    """Universal class for documenting errors in FastAPI endpoints.

    Works with any FastAPI project. Can accept:
    - Standard HTTP statuses via boolean flags
    - Dict in FastAPI responses format
    - Objects implementing ErrorDTO protocol (for project compatibility)

    Implements Mapping protocol, so can be used directly in FastAPI responses
    parameter without calling ().

    Example:
        ```python
        from fastapi import APIRouter
        from fastapi_errors_plus import Errors

        router = APIRouter()

        @router.delete(
            "/{id}",
            responses=Errors(
                {404: {                      # 404 via dict (positional first)
                    "description": "Not found",
                    "content": {
                        "application/json": {
                            "example": {"detail": "Item not found"},
                        },
                    },
                }},
                unauthorized_401=True,      # 401 (explicit, named after positional)
                forbidden_403=True,          # 403 (explicit)
                # validation_error_422=True - not needed, defaults to True
            ),
        )
        def delete_item(id: int):
            pass
        ```
    """

    # Standard descriptions for priority checking (same mapping as module constant).
    STANDARD_DESCRIPTIONS = _STANDARD_DESCRIPTIONS

    def __init__(
        self,
        # Arbitrary errors (dict or ErrorDTO) - must come first
        *errors: Union[Dict[int, Dict[str, Any]], ErrorDTO],
        # Standard HTTP statuses (boolean flags)
        # Old parameters (for backward compatibility)
        unauthorized: bool = False,  # 401
        forbidden: bool = False,  # 403
        validation_error: Optional[
            bool
        ] = None,  # 422 (None = use default True, False = disable, True = enable)
        internal_server_error: bool = False,  # 500
        # New parameters with explicit status codes (recommended)
        unauthorized_401: Optional[bool] = None,  # 401 (explicit)
        forbidden_403: Optional[bool] = None,  # 403 (explicit)
        validation_error_422: Optional[
            bool
        ] = None,  # 422 (explicit, None = use default True, False = disable, True = enable)
        internal_server_error_500: Optional[bool] = None,  # 500 (explicit)
        profile: Optional[ErrorProfile] = None,
    ) -> None:
        """Initialize Errors instance.

        Args:
            *errors: Arbitrary errors as dict or ErrorDTO objects.
                Dict should be in FastAPI responses format: {status_code: {...}}.
                ErrorDTO objects must implement the ErrorDTO protocol.
            unauthorized: Add 401 Unauthorized error. Defaults to False.
                Deprecated: Use `unauthorized_401` instead for explicit status code.
            forbidden: Add 403 Forbidden error. Defaults to False.
                Deprecated: Use `forbidden_403` instead for explicit status code.
            validation_error: Add 422 Unprocessable Entity error.
                - None (default): Add 422 (True by default, FastAPI validates all parameters)
                - False: Explicitly disable 422
                - True: Explicitly enable 422
                FastAPI automatically validates all parameters (Path, Query, Body), so 422 is relevant
                in 95%+ of endpoints. Set to False only for endpoints without parameters.
                Deprecated: Use `validation_error_422` instead for explicit status code.
            internal_server_error: Add 500 Internal Server Error. Defaults to False.
                Deprecated: Use `internal_server_error_500` instead for explicit status code.
            unauthorized_401: Add 401 Unauthorized error (explicit). None means "use profile/default".
            forbidden_403: Add 403 Forbidden error (explicit). None means "use profile/default".
            validation_error_422: Add 422 Unprocessable Entity error (explicit).
                - None (default): Add 422 (True by default, FastAPI validates all parameters)
                - False: Explicitly disable 422
                - True: Explicitly enable 422
                FastAPI automatically validates all parameters (Path, Query, Body), so 422 is relevant
                in 95%+ of endpoints. Set to False only for endpoints without parameters.
            internal_server_error_500: Add 500 Internal Server Error (explicit). None means "use profile/default".

        Example:
            ```python
            # Standard flags only
            errors = Errors(unauthorized=True, forbidden=True)

            # Dict errors
            errors = Errors({404: {"description": "Not found", ...}})

            # ErrorDTO
            errors = Errors(MyErrorDTO())

            # Mixed
            errors = Errors(
                {409: {...}},
                MyErrorDTO(),
                unauthorized=True,
            )
            ```
        """
        flags = resolve_standard_flags(
            unauthorized=unauthorized,
            forbidden=forbidden,
            validation_error=validation_error,
            internal_server_error=internal_server_error,
            unauthorized_401=unauthorized_401,
            forbidden_403=forbidden_403,
            validation_error_422=validation_error_422,
            internal_server_error_500=internal_server_error_500,
            profile=profile,
        )

        state = MergeState()

        if flags.unauthorized_401:
            add_standard_error(
                state,
                status.HTTP_401_UNAUTHORIZED,
                "Unauthorized",
                {"detail": "Unauthorized"},
            )
        if flags.forbidden_403:
            add_standard_error(
                state,
                status.HTTP_403_FORBIDDEN,
                "Forbidden",
                {"detail": "Forbidden"},
            )
        if flags.validation_error_422:
            add_standard_error(
                state,
                _HTTP_422,
                "Validation Error",
                {"detail": "Validation error"},
            )
        if flags.internal_server_error_500:
            add_standard_error(
                state,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Internal Server Error",
                {"detail": "Internal Server Error"},
            )

        for error in errors:
            if isinstance(error, dict):
                add_dict_error(state, error)
            else:
                self._validate_error_dto(error)
                add_error_dto(
                    state,
                    error,
                    standard_descriptions=_STANDARD_DESCRIPTIONS,
                )

        ensure_response_descriptions(state.responses)
        self._responses = state.responses
        self._flag_example_keys = state.flag_example_keys

    def _validate_error_dto(self, error: Any) -> None:
        """Validate that error object implements ErrorDTO or LegacyErrorDTO protocol."""
        has_to_examples = callable(getattr(error, "to_examples", None))
        has_to_example = callable(getattr(error, "to_example", None))

        if isinstance(error, ErrorDTO) and has_to_examples:
            return
        if isinstance(error, LegacyErrorDTO) and has_to_example:
            return

        required_attrs = ("status_code", "message")
        missing_attrs = [attr for attr in required_attrs if not hasattr(error, attr)]
        if not has_to_examples and not has_to_example:
            missing_methods = ["to_examples or to_example"]
        else:
            missing_methods = []

        if missing_attrs or missing_methods:
            missing = missing_attrs + missing_methods
            raise TypeError(
                f"ErrorDTO object must have {', '.join(required_attrs)} attributes "
                f"and to_examples() or to_example() method. "
                f"Missing: {', '.join(missing)}. "
                f"Got {type(error).__name__}"
            )

    def _unique_key(self, examples: Dict[str, Any], base: str) -> str:
        """Generate unique key for examples dict (delegates to :func:`unique_key`)."""
        return unique_key(examples, base)

    # Mapping protocol implementation
    def __getitem__(self, key: int) -> Dict[str, Any]:
        """Get response for status code.

        Args:
            key: HTTP status code (e.g., 401, 403, 404)

        Returns:
            Response dict in FastAPI format

        Raises:
            KeyError: If status code not found
        """
        return copy.deepcopy(self._responses[key])

    def __iter__(self) -> Iterator[int]:
        """Iterate over status codes.

        Returns:
            Iterator over status codes
        """
        return iter(self._responses)

    def __len__(self) -> int:
        """Get number of status codes.

        Returns:
            Number of documented error status codes
        """
        return len(self._responses)
