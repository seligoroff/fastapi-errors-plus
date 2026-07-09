# fastapi-errors-plus

[![PyPI version](https://badge.fury.io/py/fastapi-errors-plus.svg)](https://pypi.org/project/fastapi-errors-plus/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-154-success.svg)](https://github.com/seligoroff/fastapi-errors-plus)
[![Coverage](https://img.shields.io/badge/coverage-80%25%2B-green.svg)](https://github.com/seligoroff/fastapi-errors-plus)

Universal library for documenting errors in FastAPI endpoints.

> [Русская версия README](https://github.com/seligoroff/fastapi-errors-plus/blob/main/README.ru.md)

**Docs policy:** substantive documentation changes are applied to both `README.md` (English) and `README.ru.md` (Russian).

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
        # validation_error_422=True - opt in when documenting 422
    ),
)
def delete_item(id: int):
    """Delete an item."""
    # ... your code ...
    pass
```

## Recommended Path

For new endpoints, prefer **`ErrorDoc`** or **domain exceptions** implementing **`ErrorDTO`**. Use **`ErrorProfile`** for project-wide defaults. **`BaseErrorDTO`** / **`StandardErrorDTO`**, boolean flags (`*_401`, …), and raw OpenAPI dicts are composable in one `Errors(...)` call.

### ErrorDoc

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

### Domain exceptions as ErrorDTO

Make domain exceptions implement **`ErrorDTO`** so runtime errors and OpenAPI docs share one type:

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
        NotificationNotFoundError.for_openapi(),
    ),
)
async def delete_notification(notification_id: str):
    if not notification:
        raise NotificationNotFoundError(notification_id)
```

See [examples/domain_exceptions.py](examples/domain_exceptions.py) for a full walkthrough.

### ErrorProfile

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

### Bundled DTOs (`BaseErrorDTO`, `StandardErrorDTO`)

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

@router.post("/items", responses=Errors(business_conflict, validation_error_422=False))
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
        # validation_error_422=True - opt in when documenting 422
    ),
)
def delete_item(id: int):
    """Delete an item."""
    pass
```

`examples` values may be **strings** (shorthand for `{"detail": text}`) or full OpenAPI Example Objects with **`summary`** and **`value`**.

### Standard HTTP flags

Use boolean flags for common HTTP status codes:

- `unauthorized_401=True` → 401 Unauthorized
- `forbidden_403=True` → 403 Forbidden
- `validation_error_422=True` → 422 Unprocessable Entity (opt-in; default is **not** to add 422)
- `internal_server_error_500=True` → 500 Internal Server Error

**Note on 422:** By default, `Errors()` does **not** add a 422 response. Pass `validation_error_422=True` (or set `ErrorProfile(validation_error_422=True)`) for endpoints where you want a documented validation error. For ADR-style APIs that document domain error bodies instead of generic 422, keep `validation_error_422=False` explicitly or via profile. This disables only the **library-managed** 422 entry; FastAPI may still return auto-422 `HTTPValidationError` for invalid parameters — treat those as separate concerns in contract tests.

```python
@router.get(
    "/protected",
    responses=Errors(
        unauthorized_401=True,
        forbidden_403=True,
    ),
)
def get_protected():
    """Protected endpoint."""
    pass
```

### Dict-based errors

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

### Custom `ErrorDTO` implementations

The canonical **`ErrorDTO`** protocol:

```python
from typing import Protocol, Dict, Any

class ErrorDTO(Protocol):
    status_code: int
    message: str

    def to_examples(self) -> Dict[str, Any]:
        """OpenAPI ``examples`` map: {"Key": {"value": {...}, "summary": "..."}}."""
        ...
```

Any class implementing this protocol (structural typing) can be used with `Errors()`:

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

**Use Protocol (structural typing)** when you already have error DTOs or need custom logic. **Use `ErrorDoc` / bundled DTOs** when starting fresh or documenting multiple examples per status. Both can be mixed in one `Errors()` call.

Optional on custom DTOs: **`openapi_json_extras`** or **`to_openapi_json_media_type_extras()`** for `schema` / `encoding` beside examples.

### Combining flags, dicts, and DTOs

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
        MyErrorDTO(),
        unauthorized_401=True,
        forbidden_403=True,
        # validation_error_422=True - opt in when documenting 422
    ),
)
def create_item_mixed(id: int):
    """Create an item with mixed error types."""
    pass
```

### Merging examples and schemas

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

When merging the same status code: a **dict** wins for **`description`** over bundled standard-flag wording; an **ErrorDTO**'s `message` can replace the description only while it still matches the library's default label for that code.

Under `content["application/json"]`, `example` / `examples` are merged; later **`dict`** entries can add **`schema`**, **`encoding`**, etc. Combine one **`ErrorDTO`** with a **`dict`** for the same status listing only non-example keys:

```python
Errors(
    conflict_error_doc,
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

### Pydantic (optional)

Pydantic is **not required**. If you already use it, models with `status_code`, `message`, and `to_examples()` work through structural typing:

```python
from pydantic import BaseModel, Field
from fastapi_errors_plus import Errors
from typing import Dict, Any

class PydanticErrorDTO(BaseModel):
    status_code: int = Field(..., ge=400, le=599)
    message: str = Field(..., min_length=1)

    def to_examples(self) -> Dict[str, Any]:
        return {self.message: {"value": {"detail": self.message}}}

@router.delete("/{id}", responses=Errors(PydanticErrorDTO(status_code=404, message="Not found")))
def delete_item(id: int):
    pass
```

### Existing project DTOs

If your project already has error DTOs (like `ApiErrorDTO`), they work when they implement **`ErrorDTO`**:

```python
@dataclass
class ApiErrorDTO:
    status_code: int
    message: str

    def to_examples(self) -> dict:
        return {self.message: {"value": {"detail": self.message}}}

@router.delete("/{id}", responses=Errors(ApiErrorDTO(status_code=404, message="Not found")))
def delete_item(id: int):
    pass
```

## API Reference

### `Errors`

Main class for documenting errors in FastAPI endpoints.

#### Constructor

```python
from typing import Any, Dict, Optional, Union

class Errors:
    def __init__(
        self,
        *errors: Union[Dict[int, Dict[str, Any]], "ErrorDTO"],
        unauthorized_401: Optional[bool] = None,
        forbidden_403: Optional[bool] = None,
        validation_error_422: Optional[bool] = None,
        internal_server_error_500: Optional[bool] = None,
        profile: Optional["ErrorProfile"] = None,
    ) -> None:
        ...
```

**Parameters:**
- `*errors`: Arbitrary errors as dict or ErrorDTO objects
- `unauthorized_401`: Add 401 Unauthorized error. `None` means "use profile/default" (default: do not add).
- `forbidden_403`: Add 403 Forbidden error. `None` means "use profile/default" (default: do not add).
- `validation_error_422`: Add 422 Unprocessable Entity error.
  - `None` (default): Do not add 422 unless enabled via `ErrorProfile`
  - `False`: Explicitly disable 422
  - `True`: Explicitly enable 422
- `internal_server_error_500`: Add 500 Internal Server Error. `None` means "use profile/default" (default: do not add).
- `profile`: Optional **`ErrorProfile`** — project defaults; explicit kwargs override profile.

**422 behaviour:** pass `validation_error_422=True` for endpoints with validated parameters/body where you want a documented 422 block. Use **`ErrorProfile`** to set defaults once per project.

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

During `Errors(...)` initialization, non-`dict` objects in `*errors` missing `status_code`, `message`, or a callable **`to_examples()`** raise **`TypeError`** naming what was missing.

### `ErrorDoc`

Declarative DTO for arbitrary example bodies and per-example **`summary`**.

**Constructor:**
```python
from typing import Any, Dict, Optional

class ErrorDoc:
    def __init__(
        self,
        status_code: int,
        message: str,
        examples: Optional[Dict[str, str | dict]] = None,
        body: Optional[Dict[str, Any]] = None,
        example_key: Optional[str] = None,
        model: Any = None,
        schema: Optional[Dict[str, Any]] = None,
        openapi_json_extras: Optional[Dict[str, Any]] = None,
    ) -> None:
        ...
```

When **`examples`** is omitted, a single example is built from **`body`** or `{"detail": message}`.

### `ErrorProfile`

Frozen project-wide defaults for standard HTTP flags.

```python
from typing import Optional

class ErrorProfile:
    def __init__(
        self,
        unauthorized_401: Optional[bool] = None,
        forbidden_403: Optional[bool] = None,
        validation_error_422: Optional[bool] = None,
        internal_server_error_500: Optional[bool] = None,
    ) -> None:
        ...
```

### `BaseErrorDTO`

Base implementation of ErrorDTO Protocol for convenience.

**Constructor:**
```python
from typing import Any, Dict, Optional

class BaseErrorDTO:
    def __init__(
        self,
        status_code: int,
        message: str,
        model: Any = None,
        schema: Optional[Dict[str, Any]] = None,
        openapi_json_extras: Optional[Dict[str, Any]] = None,
    ) -> None:
        ...
```

**Example:**
```python
error = BaseErrorDTO(status_code=404, message="Not found")
```

### `StandardErrorDTO`

Extended implementation for errors with multiple examples.

**Constructor:**
```python
from typing import Any, Dict, Optional

class StandardErrorDTO:
    def __init__(
        self,
        status_code: int,
        message: str,
        openapi_json_extras: Optional[Dict[str, Any]] = None,
        examples: Optional[Dict[str, str]] = None,
    ) -> None:
        ...
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

## Migration from 0.9

Upgrading from **0.9.x**? See **[CHANGELOG.md](CHANGELOG.md)** § 1.0.0 and the full guide **[migration-0.9-to-1.0.md](localdocs/notes/migration-0.9-to-1.0.md)**.

### Breaking changes (summary)

| Area | 0.9.x | 1.0 |
|------|-------|-----|
| `unauthorized`, `forbidden`, `validation_error`, `internal_server_error` | Deprecated, accepted | **`TypeError`** — use `*_401` / `*_403` / `*_422` / `*_500` |
| `Errors()` without 422 kwargs | Implicit 422 + warning | **No 422** |
| DTO with only `to_example()` | Works + warning | **`TypeError`** — use `to_examples()` |
| `LegacyErrorDTO`, `ErrorDTOLike` | Exported | **Removed** |

### Legacy kwargs (removed)

```python
# 0.9.x
Errors(unauthorized=True, validation_error=False)

# 1.0
Errors(unauthorized_401=True, validation_error_422=False)
```

### Implicit 422 (removed)

```python
# 0.9.x — bare Errors() documented 422
Errors()

# 1.0 — opt in
Errors(validation_error_422=True)
# or ErrorProfile(validation_error_422=True)
```

### `to_example()` (removed)

Rename custom DTO methods to **`to_examples()`**. Bundled DTOs no longer expose `to_example()`.

### Audit commands

```bash
rg 'unauthorized=|forbidden=|validation_error=|internal_server_error=' --glob '*.py'
rg 'def to_example\b' --glob '*.py'
```

Run OpenAPI diff in CI after upgrading — see the migration guide checklist.

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

## Common Pitfalls

- **Runtime vs documented divergence**: an exception can be raised at runtime but missing in
  `responses=Errors(...)` (OpenAPI won't detect this automatically).
- **`Depends()` exceptions**: auth/permission dependencies may raise 401/403, but if they are not
  declared in `Errors(...)`, the spec is incomplete.
- **Over-documented responses**: `Errors(...)` can include responses that are never raised by endpoint logic.
- **1.0 upgrade:** bare `Errors()` no longer documents 422 — add `validation_error_422=True` (or profile) where the OpenAPI contract should list validation errors.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed changelog.

