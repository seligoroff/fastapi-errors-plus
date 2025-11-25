"""Test FastAPI application for integration testing."""

from typing import Dict, Any

from fastapi import APIRouter, FastAPI, status
from fastapi_errors_plus import BaseErrorDTO, Errors, StandardErrorDTO
from tests.conftest import SimpleErrorDTO

# Create test app
app = FastAPI(title="Test API for fastapi-errors-plus")

# Create router
router = APIRouter()


# Domain Exception pattern for testing (Best Practice example)
class DomainException(Exception):
    """Base exception implementing ErrorDTO protocol."""
    status_code: int
    message: str
    
    def to_example(self) -> Dict[str, Any]:
        """Generate example for OpenAPI."""
        return {
            self.message: {
                "value": {"detail": self.message},
            },
        }
    
    @classmethod
    def for_openapi(cls):
        """Returns instance for OpenAPI documentation."""
        return cls()


class TestItemNotFoundError(DomainException):
    """Test item not found error."""
    status_code = status.HTTP_404_NOT_FOUND
    message = "Test item not found"
    
    def __init__(self, item_id: str = ""):
        self.item_id = item_id
        super().__init__(self.message)
    
    @classmethod
    def for_openapi(cls):
        """Returns instance for OpenAPI documentation."""
        return cls(item_id="test_id")


class TestItemAccessDeniedError(DomainException):
    """Test item access denied error."""
    status_code = status.HTTP_403_FORBIDDEN
    message = "Test item access denied"
    
    def __init__(self, item_id: str = "", user_id: str = ""):
        self.item_id = item_id
        self.user_id = user_id
        super().__init__(self.message)
    
    @classmethod
    def for_openapi(cls):
        """Returns instance for OpenAPI documentation."""
        return cls(item_id="test_id", user_id="test_user")


# Example 1: Standard flags only
@router.get(
    "/standard-flags",
    responses=Errors(
        unauthorized=True,
        forbidden=True,
        validation_error=True,
        internal_server_error=True,
    ),
)
def get_standard_flags():
    """Endpoint with standard HTTP status flags."""
    return {"message": "Standard flags example"}


# Example 2: Dict errors only
@router.delete(
    "/dict-errors/{item_id}",
    responses=Errors(
        {
            404: {
                "description": "Item not found",
                "content": {
                    "application/json": {
                        "example": {"detail": "Item not found"},
                    },
                },
            },
            409: {
                "description": "Conflict",
                "content": {
                    "application/json": {
                        "example": {"detail": "Item already exists"},
                    },
                },
            },
        }
    ),
)
def delete_item_dict_errors(item_id: int):
    """Endpoint with dict errors."""
    return {"message": f"Item {item_id} deleted"}


# Example 3: ErrorDTO only
@router.get(
    "/error-dto/{resource_id}",
    responses=Errors(
        SimpleErrorDTO(
            status_code=404,
            message="Resource not found",
            example_value={"detail": "Resource not found"},
        ),
    ),
)
def get_resource_error_dto(resource_id: int):
    """Endpoint with ErrorDTO."""
    return {"message": f"Resource {resource_id}"}


# Example 4: Mixed (flags + dict + ErrorDTO)
@router.post(
    "/mixed/{item_id}",
    status_code=status.HTTP_201_CREATED,
    responses=Errors(
        {409: {  # Dict
            "description": "Conflict",
            "content": {
                "application/json": {
                    "example": {"detail": "Already exists"},
                },
            },
        }},
        SimpleErrorDTO(  # ErrorDTO
            status_code=404,
            message="Not found",
            example_value={"detail": "Item not found"},
        ),
        unauthorized=True,  # Flag
        forbidden=True,  # Flag
    ),
)
def create_item_mixed(item_id: int):
    """Endpoint with mixed error types."""
    return {"message": f"Item {item_id} created"}


# Example 5: Multiple ErrorDTO with same status code (should merge)
@router.put(
    "/merge-examples/{item_id}",
    responses=Errors(
        SimpleErrorDTO(
            status_code=404,
            message="Error 1",
            example_value={"detail": "Error 1: Item not found"},
        ),
        SimpleErrorDTO(
            status_code=404,
            message="Error 2",
            example_value={"detail": "Error 2: Resource missing"},
        ),
    ),
)
def update_item_merge_examples(item_id: int):
    """Endpoint demonstrating example merging for same status code."""
    return {"message": f"Item {item_id} updated"}


# Example 6: Empty Errors (edge case)
@router.get(
    "/empty-errors",
    responses=Errors(validation_error=False),  # Explicitly disable 422 for endpoint without parameters
)
def get_empty_errors():
    """Endpoint with no errors documented."""
    return {"message": "No errors"}


# Example 7: Standard flag + dict override (should merge)
@router.delete(
    "/merge-flag-dict/{item_id}",
    responses=Errors(
        {
            401: {  # Dict overrides with multiple examples
                "description": "Unauthorized",
                "content": {
                    "application/json": {
                        "examples": {
                            "InvalidToken": {"value": {"detail": "Invalid token"}},
                            "SessionNotFound": {"value": {"detail": "Session not found"}},
                        },
                    },
                },
            },
        },
        unauthorized=True,  # Flag adds basic 401
    ),
)
def delete_item_merge_flag_dict(item_id: int):
    """Endpoint demonstrating flag + dict merge."""
    return {"message": f"Item {item_id} deleted"}


# Example 8: BaseErrorDTO
@router.get(
    "/base-error-dto/{item_id}",
    responses=Errors(
        BaseErrorDTO(
            status_code=404,
            message="Item not found",
        ),
    ),
)
def get_item_base_error_dto(item_id: int):
    """Endpoint with BaseErrorDTO."""
    return {"message": f"Item {item_id}"}


# Example 9: StandardErrorDTO with multiple examples
@router.delete(
    "/standard-error-dto/{item_id}",
    responses=Errors(
        StandardErrorDTO(
            status_code=401,
            message="Unauthorized",
            examples={
                "InvalidToken": "Ошибка декодирования токена.",
                "SessionNotFound": "Сессия пользователя не была найдена.",
            },
        ),
        StandardErrorDTO(
            status_code=403,
            message="Forbidden",
            examples={
                "AccountNotSelected": "Аккаунт не выбран.",
                "RoleHasNoAccess": "Роль не имеет доступа.",
            },
        ),
    ),
)
def delete_item_standard_error_dto(item_id: int):
    """Endpoint with StandardErrorDTO."""
    return {"message": f"Item {item_id} deleted"}


# Example 10: Mixed BaseErrorDTO + StandardErrorDTO + flags
@router.post(
    "/mixed-base-dto/{item_id}",
    responses=Errors(
        BaseErrorDTO(
            status_code=404,
            message="Item not found",
        ),
        StandardErrorDTO(
            status_code=401,
            message="Unauthorized",
            examples={
                "InvalidToken": "Invalid token",
            },
        ),
        validation_error=True,
        internal_server_error=True,
    ),
)
def create_item_mixed_base_dto(item_id: int):
    """Endpoint with mixed BaseErrorDTO, StandardErrorDTO, and flags."""
    return {"message": f"Item {item_id} created"}


# Domain Exception pattern for testing (Best Practice example)
class DomainException(Exception):
    """Base exception implementing ErrorDTO protocol."""
    status_code: int
    message: str
    
    def to_example(self) -> Dict[str, Any]:
        """Generate example for OpenAPI."""
        return {
            self.message: {
                "value": {"detail": self.message},
            },
        }
    
    @classmethod
    def for_openapi(cls):
        """Returns instance for OpenAPI documentation."""
        return cls()


class TestItemNotFoundError(DomainException):
    """Test item not found error."""
    status_code = status.HTTP_404_NOT_FOUND
    message = "Test item not found"
    
    def __init__(self, item_id: str = ""):
        self.item_id = item_id
        super().__init__(self.message)
    
    @classmethod
    def for_openapi(cls):
        """Returns instance for OpenAPI documentation."""
        return cls(item_id="test_id")


class TestItemAccessDeniedError(DomainException):
    """Test item access denied error."""
    status_code = status.HTTP_403_FORBIDDEN
    message = "Test item access denied"
    
    def __init__(self, item_id: str = "", user_id: str = ""):
        self.item_id = item_id
        self.user_id = user_id
        super().__init__(self.message)
    
    @classmethod
    def for_openapi(cls):
        """Returns instance for OpenAPI documentation."""
        return cls(item_id="test_id", user_id="test_user")


# Example 11: Domain Exception as ErrorDTO (Best Practice pattern)
@router.delete(
    "/domain-exception/{item_id}",
    responses=Errors(
        TestItemNotFoundError.for_openapi(),      # Using for_openapi() pattern
        TestItemAccessDeniedError.for_openapi(),  # Using for_openapi() pattern
        unauthorized_401=True,                    # Standard flag
    ),
)
def delete_item_domain_exception(item_id: str):
    """Endpoint demonstrating Domain Exception as ErrorDTO pattern."""
    return {"message": f"Item {item_id} deleted"}


# Register router
app.include_router(router, prefix="/api/v1", tags=["test"])

