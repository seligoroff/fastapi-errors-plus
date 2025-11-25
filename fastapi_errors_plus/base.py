"""Base implementations of ErrorDTO protocol for convenience."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class BaseErrorDTO:
    """Base implementation of ErrorDTO Protocol.
    
    Projects can use this class directly or create their own implementation
    that implements ErrorDTO Protocol through structural typing.
    
    This class provides a simple way to create error DTOs without writing
    boilerplate code in every project.
    
    Example:
        ```python
        from fastapi_errors_plus import Errors, BaseErrorDTO
        
        notification_error = BaseErrorDTO(
            status_code=404,
            message="Notification not found",
        )
        
        @router.delete(
            "/{id}",
            responses=Errors(notification_error),
        )
        def delete_item(id: int):
            pass
        ```
    """
    status_code: int
    """HTTP status code for the error."""
    
    message: str
    """Error message description."""
    
    def to_example(self) -> Dict[str, Any]:
        """Generate example for OpenAPI.
        
        Returns:
            Dict in format: {"key": {"value": {"detail": "message"}}}
            
        Example:
            ```python
            {
                "Notification not found": {
                    "value": {"detail": "Notification not found"},
                },
            }
            ```
        """
        return {
            self.message: {
                "value": {"detail": self.message},
            },
        }


@dataclass
class StandardErrorDTO(BaseErrorDTO):
    """Extended implementation for errors with multiple examples.
    
    Useful for standard HTTP errors (401, 403) that can have different
    causes with different messages.
    
    Example:
        ```python
        from fastapi_errors_plus import Errors, StandardErrorDTO
        
        unauthorized_error = StandardErrorDTO(
            status_code=401,
            message="Unauthorized",
            examples={
                "InvalidToken": "Ошибка декодирования токена.",
                "SessionNotFound": "Сессия пользователя не была найдена.",
            },
        )
        
        @router.delete(
            "/{id}",
            responses=Errors(unauthorized_error),
        )
        def delete_item(id: int):
            pass
        ```
    """
    examples: Optional[Dict[str, str]] = field(default=None)
    """Dictionary of examples: {"key": "message"}."""
    
    def __post_init__(self) -> None:
        """Initialize examples with default value if not provided."""
        if self.examples is None:
            self.examples = {self.message: self.message}
    
    def to_example(self) -> Dict[str, Any]:
        """Generate examples for OpenAPI with multiple examples.
        
        Returns:
            Dict in format: {"key": {"value": {"detail": "message"}}, ...}
            
        Example:
            ```python
            {
                "InvalidToken": {
                    "value": {"detail": "Ошибка декодирования токена."},
                },
                "SessionNotFound": {
                    "value": {"detail": "Сессия пользователя не была найдена."},
                },
            }
            ```
        """
        return {
            key: {
                "value": {"detail": message},
            }
            for key, message in self.examples.items()
        }



