"""Universal library for documenting errors in FastAPI endpoints."""

from fastapi_errors_plus.errors import Errors
from fastapi_errors_plus.protocol import ErrorDTO

__all__ = ["Errors", "ErrorDTO"]
__version__ = "0.1.0"

