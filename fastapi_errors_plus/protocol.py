"""Protocol for error DTOs compatible with fastapi-errors-plus."""

from typing import Any, Dict, Protocol


class ErrorDTO(Protocol):
    """Protocol for error objects compatible with the library.
    
    Any class implementing this protocol can be used with Errors().
    
    Example:
        ```python
        class MyError:
            status_code = 404
            message = "Not found"
            
            def to_example(self) -> Dict[str, Any]:
                return {
                    "Not found": {
                        "value": {"detail": "Not found"},
                    },
                }
        
        errors = Errors(MyError())
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
                "Not found": {
                    "value": {"detail": "Not found"},
                },
            }
            ```
        """
        ...

