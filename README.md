# fastapi-errors-plus

[![PyPI version](https://badge.fury.io/py/fastapi-errors-plus.svg)](https://pypi.org/project/fastapi-errors-plus/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-41%20passed-success.svg)](https://github.com/yourusername/fastapi-errors-plus)
[![Coverage](https://img.shields.io/badge/coverage-83%25-green.svg)](https://github.com/yourusername/fastapi-errors-plus)

Universal library for documenting errors in FastAPI endpoints.

> [Русская версия README](README.ru.md)

## Philosophy

`fastapi-errors-plus` is designed to be **universal** and work with **any** FastAPI project without requiring project-specific infrastructure. The library uses standard Python types (dict, Protocol) and allows projects to adapt their existing error infrastructure to work with the library through structural typing.

**Key principles:**
- **Universality** — works with any FastAPI project
- **Transparency** — all documented errors are visible directly in the endpoint
- **Self-sufficiency** — no need to search other files to understand documented errors
- **Compatibility** — works with existing project infrastructure through Protocol

## Installation

```bash
pip install fastapi-errors-plus
```

Or install from source:

```bash
git clone https://github.com/yourusername/fastapi-errors-plus.git
cd fastapi-errors-plus
pip install -e .
```

## Quick Start

### Basic Usage

```python
from fastapi import APIRouter
from fastapi_errors_plus import Errors

router = APIRouter()

@router.delete(
    "/{id}",
    responses=Errors(
        {404: {                      # 404 via dict
            "description": "Not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Item not found"},
                },
            },
        }},
        unauthorized=True,           # 401 Unauthorized
        forbidden=True,               # 403 Forbidden
        validation_error=True,       # 422 Validation Error
    ),
)
def delete_item(id: int):
    """Delete an item."""
    # ... your code ...
    pass
```

## Features

### 1. Standard HTTP Status Flags

Use boolean flags for common HTTP status codes:

- `unauthorized=True` → 401 Unauthorized
- `forbidden=True` → 403 Forbidden
- `validation_error=True` → 422 Unprocessable Entity
- `internal_server_error=True` → 500 Internal Server Error

```python
@router.get(
    "/protected",
    responses=Errors(
        unauthorized=True,
        forbidden=True,
    ),
)
def get_protected():
    """Protected endpoint."""
    pass
```

### 2. Dict-based Errors

Use standard FastAPI `responses` dict format for custom errors:

```python
@router.post(
    "/items",
    responses=Errors(
        {
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
def create_item():
    """Create an item."""
    pass
```

### 3. ErrorDTO Protocol

Use objects implementing the `ErrorDTO` protocol for project compatibility:

```python
from fastapi_errors_plus import Errors, ErrorDTO

class MyErrorDTO:
    status_code = 404
    message = "Not found"
    
    def to_example(self):
        return {
            "Not found": {
                "value": {"detail": "Not found"},
            },
        }

@router.get(
    "/resource/{id}",
    responses=Errors(
        MyErrorDTO(),
    ),
)
def get_resource(id: int):
    """Get a resource."""
    pass
```

### 4. Mixed Usage

Combine flags, dict, and ErrorDTO:

```python
@router.post(
    "/items/{id}",
    responses=Errors(
        {409: {
            "description": "Conflict",
            "content": {
                "application/json": {
                    "example": {"detail": "Already exists"},
                },
            },
        }},
        MyErrorDTO(),  # ErrorDTO
        unauthorized=True,  # Flag
        forbidden=True,  # Flag
    ),
)
def create_item_mixed(id: int):
    """Create an item with mixed error types."""
    pass
```

### 5. Merging Examples

Multiple errors with the same status code are automatically merged:

```python
@router.put(
    "/items/{id}",
    responses=Errors(
        Error1(),  # 404
        Error2(),  # 404
    ),
)
def update_item(id: int):
    """Update an item."""
    pass
```

The OpenAPI spec will contain both examples under the 404 status code.

## ErrorDTO Protocol

The `ErrorDTO` protocol defines the interface for error objects compatible with the library:

```python
from typing import Protocol, Dict, Any

class ErrorDTO(Protocol):
    status_code: int
    message: str
    
    def to_example(self) -> Dict[str, Any]:
        """Generate example for OpenAPI.
        
        Returns:
            Dict in format: {"key": {"value": {"detail": "message"}}}
        """
        ...
```

Any class implementing this protocol (through structural typing) can be used with `Errors()`.

## Compatibility with Existing Projects

If your project already has error DTOs (like `ApiErrorDTO`), they can work with `fastapi-errors-plus` if they implement the `ErrorDTO` protocol:

```python
# Your existing ApiErrorDTO
@dataclass
class ApiErrorDTO:
    status_code: int
    message: str
    
    def to_example(self) -> dict:
        return {
            self.message: {
                "value": {"detail": self.message},
            },
        }

# Works directly with fastapi-errors-plus!
@router.delete(
    "/{id}",
    responses=Errors(
        ApiErrorDTO(status_code=404, message="Not found"),
    ),
)
def delete_item(id: int):
    pass
```

## API Reference

### `Errors`

Main class for documenting errors in FastAPI endpoints.

#### Constructor

```python
Errors(
    *errors: Union[Dict[int, Dict[str, Any]], ErrorDTO],
    unauthorized: bool = False,
    forbidden: bool = False,
    validation_error: bool = False,
    internal_server_error: bool = False,
)
```

**Parameters:**
- `*errors`: Arbitrary errors as dict or ErrorDTO objects
- `unauthorized`: Add 401 Unauthorized error
- `forbidden`: Add 403 Forbidden error
- `validation_error`: Add 422 Unprocessable Entity error
- `internal_server_error`: Add 500 Internal Server Error

**Returns:**
- Callable object that returns `Dict[int, Dict[str, Any]]` in FastAPI responses format

#### Usage

```python
# Call the instance to get responses dict
responses = Errors(unauthorized=True)
```

### `ErrorDTO`

Protocol for error objects compatible with the library.

**Required attributes:**
- `status_code: int` — HTTP status code
- `message: str` — Error message description

**Required methods:**
- `to_example() -> Dict[str, Any]` — Generate example for OpenAPI

## Examples

### Example 1: Standard FastAPI Project

```python
from fastapi import APIRouter
from fastapi_errors_plus import Errors

router = APIRouter()

@router.delete(
    "/{id}",
    responses=Errors(
        {404: {
            "description": "Not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Item not found"},
                },
            },
        }},
        unauthorized=True,
        forbidden=True,
    ),
)
def delete_item(id: int):
    """Delete an item."""
    pass
```

### Example 2: Project with ErrorDTO

```python
from fastapi import APIRouter
from fastapi_errors_plus import Errors
from api.exceptions.dto import errors  # Your project's error DTOs

router = APIRouter()

@router.delete(
    "/{notificationId}",
    responses=Errors(
        unauthorized=True,
        forbidden=True,
        errors.notification_not_found_error,  # Your ErrorDTO
    ),
)
async def delete_notification(notification_id: int):
    """Delete a notification."""
    pass
```

### Example 3: Multiple Examples for Same Status

```python
@router.delete(
    "/{id}",
    responses=Errors(
        unauthorized=True,  # Basic 401
        {401: {  # Override with multiple examples
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "examples": {
                        "InvalidToken": {"value": {"detail": "Invalid token"}},
                        "SessionNotFound": {"value": {"detail": "Session not found"}},
                    },
                },
            },
        }},
    ),
)
def delete_item(id: int):
    """Delete an item."""
    pass
```

### Example 4: Clean Architecture Integration

This example shows how to use `fastapi-errors-plus` in a FastAPI project with Clean Architecture:

**Domain Layer** (`domain/errors.py`):
```python
from typing import Protocol, Dict, Any

class DomainError(Protocol):
    """Domain error protocol compatible with ErrorDTO."""
    status_code: int
    message: str
    
    def to_example(self) -> Dict[str, Any]:
        """Generate example for OpenAPI."""
        ...

class ItemNotFoundError:
    """Domain error for item not found."""
    status_code = 404
    message = "Item not found"
    
    def to_example(self) -> Dict[str, Any]:
        return {
            "ItemNotFound": {
                "value": {"detail": "Item not found"},
            },
        }

class ItemAlreadyExistsError:
    """Domain error for item already exists."""
    status_code = 409
    message = "Item already exists"
    
    def to_example(self) -> Dict[str, Any]:
        return {
            "ItemAlreadyExists": {
                "value": {"detail": "Item already exists"},
            },
        }
```

**Application Layer** (`application/use_cases.py`):
```python
from domain.errors import ItemNotFoundError, ItemAlreadyExistsError

class CreateItemUseCase:
    """Use case for creating an item."""
    
    def execute(self, item_data: dict):
        # Business logic here
        if self._item_exists(item_data["id"]):
            raise ItemAlreadyExistsError()
        # ... create item ...
        return item

class GetItemUseCase:
    """Use case for getting an item."""
    
    def execute(self, item_id: int):
        item = self._repository.get(item_id)
        if not item:
            raise ItemNotFoundError()
        return item
```

**Infrastructure/Presentation Layer** (`api/routes/items.py`):
```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_errors_plus import Errors
from domain.errors import ItemNotFoundError, ItemAlreadyExistsError
from application.use_cases import CreateItemUseCase, GetItemUseCase

router = APIRouter()

@router.post(
    "/items",
    status_code=status.HTTP_201_CREATED,
    responses=Errors(
        unauthorized=True,  # From authentication dependency
        forbidden=True,     # From authorization dependency
        validation_error=True,  # From FastAPI validation
        ItemAlreadyExistsError(),  # Domain error
    ),
)
async def create_item(
    item_data: dict,
    use_case: CreateItemUseCase = Depends(),
):
    """Create a new item."""
    try:
        item = use_case.execute(item_data)
        return item
    except ItemAlreadyExistsError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )

@router.get(
    "/items/{item_id}",
    responses=Errors(
        unauthorized=True,
        forbidden=True,
        ItemNotFoundError(),  # Domain error
    ),
)
async def get_item(
    item_id: int,
    use_case: GetItemUseCase = Depends(),
):
    """Get an item by ID."""
    try:
        item = use_case.execute(item_id)
        return item
    except ItemNotFoundError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )
```

**Benefits of this approach:**
- Domain errors are reusable across layers
- Errors are documented directly in the endpoint
- Clean separation of concerns
- Domain layer doesn't depend on FastAPI
- Easy to test domain errors independently

## Limitations

The library improves **transparency of documented** errors. It does **not** solve the problem of finding **all real** errors in an endpoint, which requires analyzing the entire codebase (transaction scripts, `Depends` dependencies, database operations, etc.).

**What the library does:**
- Improves transparency of documented errors
- Simplifies syntax for documenting errors
- Makes errors visible directly in the endpoint

**What the library does not do:**
- Find all real errors in an endpoint automatically
- Analyze code to discover errors
- Guarantee completeness of error lists

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed changelog.

