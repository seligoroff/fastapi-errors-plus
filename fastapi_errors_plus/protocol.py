"""Protocol for error DTOs compatible with fastapi-errors-plus."""

from typing import Any, Dict, Protocol


class ErrorDTO(Protocol):
    """Protocol for error objects compatible with the library.
    
    Any class implementing this protocol can be used with Errors().
    
    Optionally, objects may expose **OpenAPI extras** besides examples:
    
    - ``openapi_json_extras``: ``dict`` merged into ``content["application/json"]``  
      (e.g. ``{"schema": ...}`` — do **not** use for ``example`` / ``examples``).
    - or ``to_openapi_json_media_type_extras() -> Optional[dict]``: if present and returns a
      non-empty ``dict``, it **takes precedence** over ``openapi_json_extras``.
    
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





