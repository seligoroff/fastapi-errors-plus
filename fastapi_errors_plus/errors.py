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
from fastapi_errors_plus._dto_validation import validate_error_dto
from fastapi_errors_plus._flags_and_profile import resolve_standard_flags
from fastapi_errors_plus._legacy_kwargs import reject_legacy_errors_kwargs
from fastapi_errors_plus._merge_engine import (
    MergeState,
    add_dict_error,
    add_error_dto,
    add_standard_error,
)
from fastapi_errors_plus._standard_errors import (
    standard_validation_error_example,
    standard_validation_error_openapi_json_extras,
)
from fastapi_errors_plus.error_profile import ErrorProfile
from fastapi_errors_plus.protocol import ErrorDTO


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
                # validation_error_422=True - opt in when documenting 422
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
        *errors: Union[Dict[int, Dict[str, Any]], ErrorDTO],
        unauthorized_401: Optional[bool] = None,
        forbidden_403: Optional[bool] = None,
        validation_error_422: Optional[bool] = None,
        internal_server_error_500: Optional[bool] = None,
        profile: Optional[ErrorProfile] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Errors instance.

        Args:
            *errors: Arbitrary errors as dict or ErrorDTO objects.
                Dict should be in FastAPI responses format: {status_code: {...}}.
                ErrorDTO objects must implement the ErrorDTO protocol.
            unauthorized_401: Add 401 Unauthorized error. None means "use profile/default".
            forbidden_403: Add 403 Forbidden error. None means "use profile/default".
            validation_error_422: Add 422 Unprocessable Entity error (explicit).
                - None (default): Do not add 422 unless enabled via profile
                - False: Explicitly disable 422
                - True: Explicitly enable 422
            internal_server_error_500: Add 500 Internal Server Error. None means "use profile/default".

        Example:
            ```python
            errors = Errors(unauthorized_401=True, forbidden_403=True)
            errors = Errors({404: {"description": "Not found", ...}})
            errors = Errors(MyErrorDTO())
            ```
        """
        reject_legacy_errors_kwargs(kwargs)

        flags = resolve_standard_flags(
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
                standard_validation_error_example(),
                application_json_extras=standard_validation_error_openapi_json_extras(),
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
                validate_error_dto(error)
                add_error_dto(
                    state,
                    error,
                )

        ensure_response_descriptions(state.responses)
        self._responses = state.responses

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
