"""Test FastAPI application for integration testing."""

from fastapi import APIRouter, FastAPI, status
from fastapi_errors_plus import Errors
from tests.conftest import SimpleErrorDTO

# Create test app
app = FastAPI(title="Test API for fastapi-errors-plus")

# Create router
router = APIRouter()


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
    responses=Errors(),
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


# Register router
app.include_router(router, prefix="/api/v1", tags=["test"])

