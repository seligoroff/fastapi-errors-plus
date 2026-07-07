# fastapi-errors-plus

[![PyPI version](https://badge.fury.io/py/fastapi-errors-plus.svg)](https://pypi.org/project/fastapi-errors-plus/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-138-success.svg)](https://github.com/seligoroff/fastapi-errors-plus)
[![Coverage](https://img.shields.io/badge/coverage-80%25%2B-green.svg)](https://github.com/seligoroff/fastapi-errors-plus)

Universal library for documenting errors in FastAPI endpoints.

> [Русская версия README](https://github.com/seligoroff/fastapi-errors-plus/blob/main/README.ru.md)

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

**Legacy (deprecated in 0.9, removal in 1.0):**
- `unauthorized=True` → 401 Unauthorized
- `forbidden=True` → 403 Forbidden
- `validation_error=True` → 422 Unprocessable Entity
- `internal_server_error=True` → 500 Internal Server Error

**Note on 422:** If you omit both `validation_error` and `validation_error_422`, the library still adds **422** today but emits a **`DeprecationWarning`** — the default will become **`False` in 1.0**. For ADR-style APIs, set `validation_error_422=False` explicitly (or use **`ErrorProfile`** below).

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
    
    def to_examples(self):
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

#### OpenAPI extras (`schema`) next to examples

ADR-style payloads (`code`, `detail`, optional `context`) need a **`schema`** in the spec besides **`examples`**. On **`BaseErrorDTO`** / **`StandardErrorDTO`** / **`ErrorDoc`** use **`openapi_json_extras`** (a dict merged under `content["application/json"]` — omit `example` / `examples` there; **`to_examples()`** still defines examples):

```python
from fastapi import APIRouter, status
from fastapi_errors_plus import BaseErrorDTO, Errors

ADR_ERROR_BODY_SCHEMA = {
    "type": "object",
    "required": ["code", "detail"],
    "properties": {
        "code": {"type": "string"},
        "detail": {"type": "string"},
        "context": {"type": "object"},
    },
}

business_conflict = BaseErrorDTO(
    status_code=status.HTTP_409_CONFLICT,
    message="BusinessRuleViolation",
    openapi_json_extras={"schema": ADR_ERROR_BODY_SCHEMA},
)

router = APIRouter()

@router.post("/items", responses=Errors(business_conflict, validation_error=False))
def create_item():
    ...
```

Custom **`ErrorDTO`** classes may instead define **`to_openapi_json_media_type_extras()`** returning a **`dict`**; if present and non-empty, it overrides **`openapi_json_extras`**. Any later **`dict`** in **`Errors`** for that status still overrides the same **`application/json`** keys (same precedence as merging two dicts).

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
- No need to write ErrorDTO classes from scratch
- Correct implementation out of the box
- Reusable across all endpoints
- Supports inheritance for custom logic

`examples` values may be **strings** (shorthand for `{"detail": text}`) or full OpenAPI Example Objects with **`summary`** and **`value`**.

#### ErrorDoc

For arbitrary response bodies (ADR `code` / `detail` / `context`, not only `detail` strings), use **`ErrorDoc`**:

```python
from fastapi_errors_plus import ErrorDoc, Errors

permission_denied = ErrorDoc(
    status_code=403,
    message="Insufficient permissions",
    examples={
        "MissingRole": {
            "summary": "User lacks required role",
            "value": {
                "code": "FORBIDDEN",
                "detail": "Role admin required",
            },
        },
    },
    openapi_json_extras={"schema": ADR_ERROR_BODY_SCHEMA},
)

@router.delete("/{id}", responses=Errors(permission_denied))
def delete_item(id: int):
    ...
```

A **plain dict** as an example value is treated as the full response **body** unless it looks like an OpenAPI Example Object (keys only among `value`, `summary`, `description`, `externalValue`).

Optional **`model=`** (Pydantic model on the outer response object for FastAPI `$ref` registration) and **`schema=`** (JSON Schema under `application/json`) avoid a separate status `dict` for typed error bodies:

```python
from fastapi_errors_plus import ErrorDoc, Errors

conflict = ErrorDoc(
    status_code=409,
    message="BusinessRule",
    model=ApplicationJsonError,  # optional Pydantic model
    schema=ADR_ERROR_BODY_SCHEMA,  # or raw JSON Schema
    body={"code": "RULE_VIOLATION", "detail": "Item exists"},
)

@router.post("/items", responses=Errors(conflict, validation_error_422=False))
def create_item():
    ...
```

#### ErrorProfile

Project-wide defaults (frozen — not mutated by endpoint calls):

```python
from fastapi_errors_plus import ErrorDoc, ErrorProfile, Errors

ADR = ErrorProfile(
    validation_error_422=False,
    unauthorized_401=True,
    internal_server_error_500=True,
)

@router.post("/items", responses=Errors(business_conflict, profile=ADR))
def create_item():
    ...
```

Explicit `Errors` keyword flags override profile values. Positional dict/DTO errors are merged after profile-driven standard statuses.

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

When merging the same status code: a **dict** wins for **`description`** over the bundled standard-flag wording; an **ErrorDTO**’s `message` can replace the description only while it still matches the library’s default label for that code (custom descriptions coming from dicts are not overwritten by DTOs).

Under `content["application/json"]`, `example` / `examples` are merged as before; any **other** OpenAPI Media Type fields from a later **`dict`** (for example **`schema`**, **`encoding`**) are **copied in** as well—the later dict wins on conflict (**same rule as `description`**).  

You can combine one **`ErrorDTO`** (examples) with a **`dict`** for the **same numeric status code** listing only **`schema`** (or other non-example keys) without repeating the boilerplate examples block:

```python
Errors(
    conflict_error_doc,   # implements ErrorDTO, e.g. .for_openapi() for ADR-shaped examples
    {
        status.HTTP_409_CONFLICT: {
            "description": "Business rule violation",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string"},
                            "detail": {"type": "string"},
                            "context": {"type": "object"},
                        },
                    },
                },
            },
        },
    },
)
```

Order matters only for overlaps: whichever **`dict`** is applied **later** in the **`Errors`** argument list overwrites **`schema`** / **`encoding`** (and **`model`** on the outer response dict, if provided) when the same keys appear again.

## ErrorDTO Protocol

The canonical **`ErrorDTO`** protocol defines the interface for error objects compatible with the library:

```python
from typing import Protocol, Dict, Any

class ErrorDTO(Protocol):
    status_code: int
    message: str
    
    def to_examples(self) -> Dict[str, Any]:
        """OpenAPI ``examples`` map: {"Key": {"value": {...}, "summary": "..."}}."""
        ...
```

Any class implementing this protocol (through structural typing) can be used with `Errors()`.

**Legacy migration:** classes that only define **`to_example()`** still work at **runtime** (`DeprecationWarning` once per class per `Errors()` call). For static typing use **`LegacyErrorDTO`** or the union alias **`ErrorDTOLike`** (`ErrorDTO | LegacyErrorDTO`).

**Best Practice:** For maximum clarity, consider making your domain exceptions implement the ErrorDTO protocol directly. See [Best Practice: Connecting Exceptions and ErrorDTO](#best-practice-connecting-exceptions-and-errordto) for details.

### When to Use Protocol vs BaseErrorDTO

Optional on custom DTOs (OpenAPI media-type extras without duplicating a status `dict`):

- attribute **`openapi_json_extras`**: fragment for **`content["application/json"]`** (often `{"schema": ...}` — not for `example` / `examples`);
- or method **`to_openapi_json_media_type_extras() -> Optional[dict]`** — when non-empty, overrides **`openapi_json_extras`**.

**Use Protocol (structural typing)** when:
- Your project already has error DTOs that implement the protocol
- You need maximum flexibility and custom implementations
- You want to keep your existing error infrastructure

**Use BaseErrorDTO/StandardErrorDTO/ErrorDoc** when:
- Starting a new project or adding error documentation
- You want a ready-to-use implementation without boilerplate
- You need multiple examples for standard HTTP errors (401, 403, etc.)

Both approaches work together — you can mix them in the same `Errors()` call!

## Using Pydantic with ErrorDTO

**Note:** Pydantic is **not required** to use this library. This section is for projects that already use Pydantic and want to integrate it with the ErrorDTO protocol.

Since the library uses structural typing (Protocol), any class that implements the required attributes (`status_code`, `message`, `to_examples()`) will work, including Pydantic models. Legacy `to_example()` is still accepted at runtime.

### Simple Pydantic Model as ErrorDTO

```python
from pydantic import BaseModel, Field
from fastapi_errors_plus import Errors
from typing import Dict, Any

class PydanticErrorDTO(BaseModel):
    """Pydantic model implementing ErrorDTO Protocol."""
    status_code: int = Field(..., ge=400, le=599, description="HTTP status code")
    message: str = Field(..., min_length=1, description="Error message")
    
    def to_examples(self) -> Dict[str, Any]:
        """Generate examples for OpenAPI."""
        return {
            self.message: {
                "value": {"detail": self.message},
            },
        }

# Usage
notification_error = PydanticErrorDTO(
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

**Benefits:**
- Runtime validation through Pydantic
- Type safety
- Automatic field documentation
- Works with ErrorDTO Protocol through structural typing

### Complex ErrorDTO with Pydantic

For errors with additional fields:

```python
from pydantic import BaseModel, Field
from fastapi_errors_plus import Errors
from typing import Dict, Any, Optional

class DetailedErrorDTO(BaseModel):
    """Pydantic model for errors with additional fields."""
    status_code: int = Field(..., ge=400, le=599)
    message: str = Field(..., min_length=1)
    error_code: Optional[str] = Field(None, description="Internal error code")
    timestamp: Optional[str] = Field(None, description="Error timestamp")
    
    def to_examples(self) -> Dict[str, Any]:
        """Generate examples for OpenAPI."""
        example = {"detail": self.message}
        if self.error_code:
            example["error_code"] = self.error_code
        if self.timestamp:
            example["timestamp"] = self.timestamp
        
        return {
            self.message: {
                "value": example,
            },
        }

# Usage
validation_error = DetailedErrorDTO(
    status_code=422,
    message="Validation failed",
    error_code="VALIDATION_ERROR",
    timestamp="2025-01-15T10:30:00Z",
)
```

**When to use Pydantic with ErrorDTO:**
- Your project already uses Pydantic extensively
- You need runtime validation for error objects
- You want automatic field documentation
- You have complex error structures with multiple fields

**When not to use Pydantic:**
- Your project doesn't use Pydantic (use `BaseErrorDTO` or `StandardErrorDTO` instead)
- You need simple error objects (dataclasses are sufficient)
- You want to keep dependencies minimal

## Best Practice: Connecting Exceptions and ErrorDTO

### Problem

It's not always clear which exception corresponds to which ErrorDTO:

```python
# Not clear which exception this documents
responses=Errors(notification_not_found_error)
```

### Solution: Domain Exception as ErrorDTO

**Recommended approach** — make your exceptions implement ErrorDTO protocol:

```python
# domain/exceptions.py
from typing import Dict, Any

class DomainException(Exception):
    """Base exception implementing ErrorDTO protocol."""
    status_code: int
    message: str
    
    def to_examples(self) -> Dict[str, Any]:
        return {self.message: {"value": {"detail": self.message}}}
    
    @classmethod
    def for_openapi(cls):
        """Returns instance for OpenAPI documentation."""
        return cls()

class NotificationNotFoundError(DomainException):
    status_code = 404
    message = "Notification not found"
    
    def __init__(self, notification_id: str = ""):
        self.notification_id = notification_id
        super().__init__(self.message)
    
    @classmethod
    def for_openapi(cls):
        return cls(notification_id="example_id")

# In endpoint
@router.delete(
    "/{notificationId}",
    responses=Errors(
        NotificationNotFoundError.for_openapi(),  # Clear connection!
    ),
)
async def delete_notification(notification_id: str):
    if not notification:
        raise NotificationNotFoundError(notification_id)  # Same exception!
```

**Benefits:**
- Exception and ErrorDTO are one class
- Clear connection visible in endpoint
- No duplication
- Type-safe
- Works with any project architecture

See [examples/domain_exceptions.py](examples/domain_exceptions.py) for complete example.

## Compatibility with Existing Projects

If your project already has error DTOs (like `ApiErrorDTO`), they can work with `fastapi-errors-plus` if they implement the `ErrorDTO` protocol (or legacy `to_example()` during migration):

```python
# Your existing ApiErrorDTO
@dataclass
class ApiErrorDTO:
    status_code: int
    message: str
    
    def to_examples(self) -> dict:
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
    profile: Optional[ErrorProfile] = None,
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
- `internal_server_error`: Add 500 Internal Server Error (legacy, **deprecated** in 0.9). Defaults to `False`.
- `profile`: Optional **`ErrorProfile`** — project defaults; explicit kwargs override profile.

**Deprecation (0.9+):** legacy kwargs above emit `DeprecationWarning` (removal in **1.0**). Omitting both `validation_error` and `validation_error_422` still adds 422 but warns; default becomes **`False` in 1.0**.

**422 behaviour:** pass `validation_error_422=False` for endpoints without request-body validation or ADR-style error bodies. Use **`ErrorProfile`** to set this once per project.

**Returns:**
- A dict-like `Mapping[int, …]` suitable for FastAPI’s `responses` / OpenAPI
- Pass the instance as-is — **do not** call it like a function: `responses=Errors(...)`

#### Usage

```python
# Instances are Mapping keyed by HTTP status codes
error_responses = Errors(unauthorized_401=True, forbidden_403=True)
documented = error_responses[401]  # deep copy — safe to read, won't mutate internal state
```

**Isolation (0.8+):** incoming response **dicts** are **deep-copied** on ingest; **`errors[status]`** returns a **deep copy** so callers cannot corrupt shared registry templates or internal merge state.

**Descriptions:** response blocks with only **`model`** (no `description`) get a default from **`HTTPStatus.phrase`** so OpenAPI generation does not fail.

### `ErrorDTO`

Protocol for error objects compatible with the library.

**Required attributes:**
- `status_code: int` — HTTP status code
- `message: str` — Error message description

**Required methods:**
- `to_examples() -> Dict[str, Any]` — OpenAPI `examples` map for `application/json`

During `Errors(...)` initialization, non-`dict` objects in `*errors` missing `status_code`, `message`, or a callable **`to_examples()`** / **`to_example()`** raise **`TypeError`** naming what was missing.

### `LegacyErrorDTO` / `ErrorDTOLike`

- **`LegacyErrorDTO`** — typing helper for classes that only implement deprecated **`to_example()`**.
- **`ErrorDTOLike`** — `Union[ErrorDTO, LegacyErrorDTO]` for transitional annotations.

### `ErrorDoc`

Declarative DTO for arbitrary example bodies and per-example **`summary`**.

**Constructor:**
```python
ErrorDoc(
    status_code: int,
    message: str,
    examples: Optional[Dict[str, str | dict]] = None,
    body: Optional[Dict[str, Any]] = None,
    example_key: Optional[str] = None,
    model: Any = None,
    schema: Optional[Dict[str, Any]] = None,
    openapi_json_extras: Optional[Dict[str, Any]] = None,
)
```

When **`examples`** is omitted, a single example is built from **`body`** or `{"detail": message}`.

### `ErrorProfile`

Frozen project-wide defaults for standard HTTP flags.

```python
ErrorProfile(
    unauthorized_401: bool = False,
    forbidden_403: bool = False,
    validation_error_422: Optional[bool] = None,
    internal_server_error_500: bool = False,
)
```

### `BaseErrorDTO`

Base implementation of ErrorDTO Protocol for convenience.

**Constructor:**
```python
BaseErrorDTO(
    status_code: int,
    message: str,
    model: Any = None,
    schema: Optional[Dict[str, Any]] = None,
    openapi_json_extras: Optional[Dict[str, Any]] = None,
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
    openapi_json_extras: Optional[Dict[str, Any]] = None,
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
from api.exceptions.dto import notification_not_found_error  # ErrorDTO-compatible instance

router = APIRouter()

@router.delete(
    "/{notificationId}",
    responses=Errors(
        unauthorized=True,
        forbidden=True,
        notification_not_found_error,
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
from typing import Dict, Any

class DomainException(Exception):
    """Domain exception usable as runtime error and shaped like ErrorDTO for OpenAPI."""
    status_code: int
    message: str

    def __init__(self) -> None:
        super().__init__(self.message)

    def to_examples(self) -> Dict[str, Any]:
        return {
            self.message: {
                "value": {"detail": self.message},
            },
        }


class ItemNotFoundError(DomainException):
    status_code = 404
    message = "Item not found"


class ItemAlreadyExistsError(DomainException):
    status_code = 409
    message = "Item already exists"
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

