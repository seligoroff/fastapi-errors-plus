"""Resolve standard HTTP flag kwargs and profile defaults for :class:`Errors` (internal)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi_errors_plus.error_profile import ErrorProfile


@dataclass(frozen=True)
class ResolvedStandardFlags:
    """Resolved boolean standard flags after profile merging."""

    unauthorized_401: bool
    forbidden_403: bool
    validation_error_422: bool
    internal_server_error_500: bool


def resolve_standard_flags(
    *,
    unauthorized_401: Optional[bool],
    forbidden_403: Optional[bool],
    validation_error_422: Optional[bool],
    internal_server_error_500: Optional[bool],
    profile: Optional[ErrorProfile],
) -> ResolvedStandardFlags:
    """Resolve standard flags from explicit kwargs and optional profile."""
    if unauthorized_401 is not None:
        use_unauthorized = unauthorized_401
    elif profile is not None:
        use_unauthorized = profile.unauthorized_401
    else:
        use_unauthorized = False

    if forbidden_403 is not None:
        use_forbidden = forbidden_403
    elif profile is not None:
        use_forbidden = profile.forbidden_403
    else:
        use_forbidden = False

    if internal_server_error_500 is not None:
        use_internal = internal_server_error_500
    elif profile is not None:
        use_internal = profile.internal_server_error_500
    else:
        use_internal = False

    if validation_error_422 is not None:
        add_422 = validation_error_422
    elif profile is not None and profile.validation_error_422 is not None:
        add_422 = profile.validation_error_422
    else:
        add_422 = False

    return ResolvedStandardFlags(
        unauthorized_401=use_unauthorized,
        forbidden_403=use_forbidden,
        validation_error_422=add_422,
        internal_server_error_500=use_internal,
    )
