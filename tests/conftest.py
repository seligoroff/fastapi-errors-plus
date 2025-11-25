"""Pytest configuration and fixtures."""

import pytest
from typing import Any, Dict

from fastapi_errors_plus import ErrorDTO


class SimpleErrorDTO:
    """Simple implementation of ErrorDTO protocol for testing."""
    
    def __init__(self, status_code: int, message: str, example_value: Dict[str, Any]):
        self.status_code = status_code
        self.message = message
        self._example_value = example_value
    
    def to_example(self) -> Dict[str, Any]:
        """Generate example for OpenAPI."""
        return {
            self.message: {
                "value": self._example_value,
            },
        }


@pytest.fixture
def simple_error_dto():
    """Fixture for creating a simple ErrorDTO instance."""
    def _create(status_code: int = 404, message: str = "Not found", detail: str = "Not found"):
        return SimpleErrorDTO(
            status_code=status_code,
            message=message,
            example_value={"detail": detail},
        )
    return _create


@pytest.fixture
def multiple_errors_dto():
    """Fixture for creating multiple ErrorDTO instances with the same status code."""
    def _create(status_code: int = 404):
        return [
            SimpleErrorDTO(
                status_code=status_code,
                message="Error 1",
                example_value={"detail": "Error 1"},
            ),
            SimpleErrorDTO(
                status_code=status_code,
                message="Error 2",
                example_value={"detail": "Error 2"},
            ),
        ]
    return _create



