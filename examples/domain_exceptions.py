"""
Example: Domain Exception as ErrorDTO

This example demonstrates the recommended approach for connecting
domain exceptions with their OpenAPI documentation.

Benefits:
- Exception and ErrorDTO are the same class
- Clear connection visible in endpoint
- No duplication
- Type-safe
- Works with any project architecture
"""

from typing import Dict, Any
from fastapi import APIRouter, status
from fastapi_errors_plus import Errors

# ============================================================================
# Domain Layer: Exceptions implementing ErrorDTO Protocol
# ============================================================================

class DomainException(Exception):
    """Base exception implementing ErrorDTO protocol.
    
    This class serves as both a runtime exception and an ErrorDTO
    for OpenAPI documentation. This eliminates the need for separate
    exception and DTO classes.
    """
    status_code: int
    message: str
    
    def to_example(self) -> Dict[str, Any]:
        """Generate example for OpenAPI.
        
        Returns:
            Dict in format: {"key": {"value": {"detail": "message"}}}
        """
        return {
            self.message: {
                "value": {"detail": self.message},
            },
        }
    
    @classmethod
    def for_openapi(cls):
        """Returns instance for OpenAPI documentation.
        
        This method should be overridden in subclasses if they require
        specific arguments for the example instance.
        """
        return cls()


class NotificationNotFoundError(DomainException):
    """Notification not found in the system."""
    status_code = status.HTTP_404_NOT_FOUND
    message = "Notification not found"
    
    def __init__(self, notification_id: str = ""):
        self.notification_id = notification_id
        super().__init__(self.message)
    
    @classmethod
    def for_openapi(cls):
        """Returns instance for OpenAPI documentation."""
        return cls(notification_id="example_id")


class NotificationAccessDeniedError(DomainException):
    """Access denied to notification."""
    status_code = status.HTTP_403_FORBIDDEN
    message = "Access denied to notification"
    
    def __init__(self, notification_id: str = "", user_id: str = ""):
        self.notification_id = notification_id
        self.user_id = user_id
        super().__init__(self.message)
    
    @classmethod
    def for_openapi(cls):
        """Returns instance for OpenAPI documentation."""
        return cls(notification_id="example_id", user_id="user_123")


# ============================================================================
# Presentation Layer: FastAPI Router
# ============================================================================

router = APIRouter()


@router.delete(
    "/{notification_id}",
    responses=Errors(
        NotificationNotFoundError.for_openapi(),      # ✅ Clear connection!
        NotificationAccessDeniedError.for_openapi(),  # ✅ Clear connection!
        unauthorized_401=True,                        # Standard flag
    ),
)
async def delete_notification(notification_id: str):
    """Delete a notification.
    
    This endpoint demonstrates how domain exceptions that implement
    ErrorDTO protocol can be used directly in FastAPI responses.
    """
    # Simulate getting notification
    notification = get_notification(notification_id)
    
    if not notification:
        # ✅ Same exception class used for both runtime and documentation!
        raise NotificationNotFoundError(notification_id)
    
    if not can_access(notification):
        # ✅ Same exception class used for both runtime and documentation!
        raise NotificationAccessDeniedError(notification_id, user_id="current_user")
    
    # Delete notification
    return {"status": "deleted"}


# ============================================================================
# Helper functions (simulated)
# ============================================================================

def get_notification(notification_id: str) -> dict:
    """Simulate getting notification."""
    if notification_id == "not_found":
        return None
    return {"id": notification_id, "content": "Example notification"}


def can_access(notification: dict) -> bool:
    """Simulate access check."""
    return notification.get("id") != "restricted"


# ============================================================================
# Exception Handlers (in your FastAPI app)
# ============================================================================

# from fastapi import Request
# from fastapi.responses import JSONResponse
# 
# @app.exception_handler(NotificationNotFoundError)
# async def notification_not_found_handler(
#     request: Request,
#     exc: NotificationNotFoundError,
# ) -> JSONResponse:
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"detail": exc.message},
#     )
# 
# @app.exception_handler(NotificationAccessDeniedError)
# async def notification_access_denied_handler(
#     request: Request,
#     exc: NotificationAccessDeniedError,
# ) -> JSONResponse:
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"detail": exc.message},
#     )

