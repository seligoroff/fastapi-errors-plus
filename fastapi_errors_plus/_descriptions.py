"""Standard and fallback response descriptions for :class:`Errors` (internal)."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any, Dict, Set

from fastapi import status

from fastapi_errors_plus._compat import HTTP_422 as _HTTP_422

STANDARD_DESCRIPTIONS: Dict[int, str] = {
    status.HTTP_401_UNAUTHORIZED: "Unauthorized",
    status.HTTP_403_FORBIDDEN: "Forbidden",
    _HTTP_422: "Validation Error",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "Internal Server Error",
}


def apply_dto_description(
    existing: Dict[str, Any],
    error_dto: Any,
    *,
    flag_description_codes: Set[int],
) -> None:
    """Set ``description`` from DTO when missing, empty, or from a standard flag."""
    desc = existing.get("description")
    if desc is None or (isinstance(desc, str) and not desc.strip()):
        existing["description"] = error_dto.message
    elif error_dto.status_code in flag_description_codes:
        existing["description"] = error_dto.message


def ensure_response_descriptions(responses: Dict[int, Dict[str, Any]]) -> None:
    """Fill missing descriptions so FastAPI OpenAPI generation does not assert."""
    for code, response in responses.items():
        desc = response.get("description")
        if desc is not None and isinstance(desc, str) and desc.strip():
            continue
        try:
            response["description"] = HTTPStatus(code).phrase
        except ValueError:
            response["description"] = f"HTTP {code}"
