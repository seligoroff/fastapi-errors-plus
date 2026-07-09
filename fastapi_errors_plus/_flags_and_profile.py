"""Resolve standard HTTP flag kwargs and profile defaults for :class:`Errors` (internal)."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Optional

from fastapi_errors_plus.error_profile import ErrorProfile

# One extra frame vs ``Errors.__init__`` so warnings still point at the caller.
_WARNING_STACKLEVEL = 3


@dataclass(frozen=True)
class ResolvedStandardFlags:
    """Resolved boolean standard flags after profile/legacy kwarg merging."""

    unauthorized_401: bool
    forbidden_403: bool
    validation_error_422: bool
    internal_server_error_500: bool


def resolve_standard_flags(
    *,
    unauthorized: bool,
    forbidden: bool,
    validation_error: Optional[bool],
    internal_server_error: bool,
    unauthorized_401: Optional[bool],
    forbidden_403: Optional[bool],
    validation_error_422: Optional[bool],
    internal_server_error_500: Optional[bool],
    profile: Optional[ErrorProfile],
) -> ResolvedStandardFlags:
    """Resolve standard flags, emitting deprecations for legacy kwargs and implicit 422."""
    if unauthorized:
        warnings.warn(
            "unauthorized is deprecated; use unauthorized_401 instead.",
            DeprecationWarning,
            stacklevel=_WARNING_STACKLEVEL,
        )
    if forbidden:
        warnings.warn(
            "forbidden is deprecated; use forbidden_403 instead.",
            DeprecationWarning,
            stacklevel=_WARNING_STACKLEVEL,
        )
    if validation_error is not None:
        warnings.warn(
            "validation_error is deprecated; use validation_error_422 instead.",
            DeprecationWarning,
            stacklevel=_WARNING_STACKLEVEL,
        )
    if internal_server_error:
        warnings.warn(
            "internal_server_error is deprecated; use internal_server_error_500 instead.",
            DeprecationWarning,
            stacklevel=_WARNING_STACKLEVEL,
        )

    if unauthorized_401 is not None:
        use_unauthorized = unauthorized_401
    elif unauthorized:
        use_unauthorized = True
    elif profile is not None:
        use_unauthorized = profile.unauthorized_401
    else:
        use_unauthorized = False

    if forbidden_403 is not None:
        use_forbidden = forbidden_403
    elif forbidden:
        use_forbidden = True
    elif profile is not None:
        use_forbidden = profile.forbidden_403
    else:
        use_forbidden = False

    if internal_server_error_500 is not None:
        use_internal = internal_server_error_500
    elif internal_server_error:
        use_internal = True
    elif profile is not None:
        use_internal = profile.internal_server_error_500
    else:
        use_internal = False

    val_422: Optional[bool]
    if validation_error_422 is not None:
        val_422 = validation_error_422
    elif validation_error is not None:
        val_422 = validation_error
    elif profile is not None:
        val_422 = profile.validation_error_422
    else:
        val_422 = None

    add_422 = True
    if val_422 is False:
        add_422 = False
    elif val_422 is None:
        add_422 = True
        warnings.warn(
            "Implicit validation_error_422=True is deprecated and will default to "
            "False in 1.0. Pass validation_error_422=False explicitly to silence.",
            DeprecationWarning,
            stacklevel=_WARNING_STACKLEVEL,
        )

    return ResolvedStandardFlags(
        unauthorized_401=use_unauthorized,
        forbidden_403=use_forbidden,
        validation_error_422=add_422,
        internal_server_error_500=use_internal,
    )
