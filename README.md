# fastapi-errors-plus

[![PyPI version](https://badge.fury.io/py/fastapi-errors-plus.svg)](https://pypi.org/project/fastapi-errors-plus/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-72%20passed-success.svg)](https://github.com/seligoroff/fastapi-errors-plus)
[![Coverage](https://img.shields.io/badge/coverage-83%25-green.svg)](https://github.com/seligoroff/fastapi-errors-plus)

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
git clone git@github.com:seligoroff/fastapi-errors-plus.git
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
        unauthorized_401=True,      # 401 Unauthorized (explicit)
        forbidden_403=True,          # 403 Forbidden (explicit)
        # validation_error_422=True - not needed, defaults to True
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

**Recommended (explicit status codes):**
- `unauthorized_401=True` → 401 Unauthorized
- `forbidden_403=True` → 403 Forbidden
- `validation_error_422=True` → 422 Unprocessable Entity (defaults to `True`)
- `internal_server_error_500=True` → 500 Internal Server Error

**Legacy (for backward compatibility):**
- `unauthorized=True` → 401 Unauthorized
- `forbidden=True` → 403 Forbidden
- `validation_error=True` → 422 Unprocessable Entity (defaults to `True`)
- `internal_server_error=True` → 500 Internal Server Error

**Note:** `validation_error` and `validation_error_422` default to `True` because FastAPI automatically validates all parameters (Path, Query, Body), making 422 relevant in 95%+ of endpoints. Set to `False` only for endpoints without parameters.

```python
@router.get(
    "/protected",
    responses=Errors(
        unauthorized_401=True,  # Explicit: 401 is visible
        forbidden_403=True,      # Explicit: 403 is visible
    ),
)
def get_protected():
    """Protected endpoint."""
    pass
```

**Why explicit flags?** The new flags with status codes (`_401`, `_403`, etc.) make it immediately clear which HTTP status code corresponds to each flag, improving code readability without needing to remember the mapping.

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

### 4. BaseErrorDTO and StandardErrorDTO (Recommended)

For convenience, the library provides ready-to-use implementations:

#### BaseErrorDTO

Simple implementation for errors with a single example:

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
    """Delete an item."""
    pass
```

#### StandardErrorDTO

Extended implementation for errors with multiple examples (useful for standard HTTP errors):

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

forbidden_error = StandardErrorDTO(
    status_code=403,
    message="Forbidden",
    examples={
        "AccountNotSelected": "Аккаунт не выбран.",
        "RoleHasNoAccess": "Роль не имеет доступа.",
    },
)

@router.delete(
    "/{id}",
    responses=Errors(
        unauthorized_error,
        forbidden_error,
        # validation_error=True - not needed, defaults to True
    ),
)
def delete_item(id: int):
    """Delete an item."""
    pass
```

**Benefits:**
- ✅ No need to write ErrorDTO classes from scratch
- ✅ Correct implementation out of the box
- ✅ Reusable across all endpoints
- ✅ Supports inheritance for custom logic

### 5. Mixed Usage

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
        # validation_error=True - not needed, defaults to True
    ),
)
def create_item_mixed(id: int):
    """Create an item with mixed error types."""
    pass
```

### 6. Merging Examples

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

### When to Use Protocol vs BaseErrorDTO

**Use Protocol (structural typing)** when:
- Your project already has error DTOs that implement the protocol
- You need maximum flexibility and custom implementations
- You want to keep your existing error infrastructure

**Use BaseErrorDTO/StandardErrorDTO** when:
- Starting a new project or adding error documentation
- You want a ready-to-use implementation without boilerplate
- You need multiple examples for standard HTTP errors (401, 403, etc.)

Both approaches work together — you can mix them in the same `Errors()` call!

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
    validation_error: Optional[bool] = None,  # None (default) => True (FastAPI validates all parameters)
    internal_server_error: bool = False,
    unauthorized_401: bool = False,
    forbidden_403: bool = False,
    validation_error_422: Optional[bool] = None,  # None (default) => True (FastAPI validates all parameters)
    internal_server_error_500: bool = False,
)
```

**Parameters:**
- `*errors`: Arbitrary errors as dict or ErrorDTO objects
- `unauthorized_401`: Add 401 Unauthorized error (recommended, explicit). Defaults to `False`.
- `forbidden_403`: Add 403 Forbidden error (recommended, explicit). Defaults to `False`.
- `validation_error_422`: Add 422 Unprocessable Entity error (recommended, explicit). 
  - `None` (default): Add 422 (True by default, FastAPI validates all parameters)
  - `False`: Explicitly disable 422
  - `True`: Explicitly enable 422
- `internal_server_error_500`: Add 500 Internal Server Error (recommended, explicit). Defaults to `False`.
- `unauthorized`: Add 401 Unauthorized error (legacy, for backward compatibility). Defaults to `False`.
- `forbidden`: Add 403 Forbidden error (legacy, for backward compatibility). Defaults to `False`.
- `validation_error`: Add 422 Unprocessable Entity error (legacy, for backward compatibility). 
  - `None` (default): Add 422 (True by default, FastAPI validates all parameters)
  - `False`: Explicitly disable 422
  - `True`: Explicitly enable 422
- `internal_server_error`: Add 500 Internal Server Error (legacy, for backward compatibility). Defaults to `False`.

**Why `validation_error=True` by default?**
FastAPI automatically validates all parameters (Path, Query, Body), so 422 is relevant in 95%+ of endpoints. For endpoints without parameters, explicitly set `validation_error=False` or `validation_error_422=False`.

**Returns:**
- Mapping object (dict-like) that implements `Dict[int, Dict[str, Any]]` for FastAPI responses
- Can be used directly in `responses` parameter without calling: `responses=Errors(...)`

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

### `BaseErrorDTO`

Base implementation of ErrorDTO Protocol for convenience.

**Constructor:**
```python
BaseErrorDTO(
    status_code: int,
    message: str,
)
```

**Example:**
```python
error = BaseErrorDTO(status_code=404, message="Not found")
```

### `StandardErrorDTO`

Extended implementation for errors with multiple examples.

**Constructor:**
```python
StandardErrorDTO(
    status_code: int,
    message: str,
    examples: Optional[Dict[str, str]] = None,
)
```

**Example:**
```python
error = StandardErrorDTO(
    status_code=401,
    message="Unauthorized",
    examples={
        "InvalidToken": "Invalid token",
        "SessionNotFound": "Session not found",
    },
)
```

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
        # validation_error=True - not needed, defaults to True (FastAPI validates all parameters)
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

