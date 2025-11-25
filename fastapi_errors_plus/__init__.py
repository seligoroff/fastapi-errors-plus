"""Universal library for documenting errors in FastAPI endpoints."""

from fastapi_errors_plus.base import BaseErrorDTO, StandardErrorDTO
from fastapi_errors_plus.errors import Errors
from fastapi_errors_plus.protocol import ErrorDTO

__all__ = [
    "Errors",
    "ErrorDTO",  # Protocol (for structural typing)
    "BaseErrorDTO",  # Base implementation (optional)
    "StandardErrorDTO",  # Extended implementation (optional)
]
__version__ = "0.5.0"

