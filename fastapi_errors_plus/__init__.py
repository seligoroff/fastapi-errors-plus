"""Universal library for documenting errors in FastAPI endpoints."""

from fastapi_errors_plus.base import BaseErrorDTO, StandardErrorDTO
from fastapi_errors_plus.error_doc import ErrorDoc
from fastapi_errors_plus.error_profile import ErrorProfile
from fastapi_errors_plus.errors import Errors
from fastapi_errors_plus.protocol import ErrorDTO, ErrorDTOLike, LegacyErrorDTO

__all__ = [
    "Errors",
    "ErrorDTO",
    "LegacyErrorDTO",
    "ErrorDTOLike",
    "ErrorDoc",
    "ErrorProfile",
    "BaseErrorDTO",
    "StandardErrorDTO",
]
__version__ = "0.9.0"
