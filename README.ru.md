# fastapi-errors-plus

[![PyPI version](https://badge.fury.io/py/fastapi-errors-plus.svg)](https://pypi.org/project/fastapi-errors-plus/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-154-success.svg)](https://github.com/seligoroff/fastapi-errors-plus)
[![Coverage](https://img.shields.io/badge/coverage-80%25%2B-green.svg)](https://github.com/seligoroff/fastapi-errors-plus)

Универсальная библиотека для документирования ошибок в эндпоинтах FastAPI.

> [English version of README](https://github.com/seligoroff/fastapi-errors-plus/blob/main/README.md)

**Политика документации:** существенные изменения вносятся синхронно в `README.md` (English) и `README.ru.md` (Russian).

## Философия

`fastapi-errors-plus` разработана как **универсальная** библиотека, которая работает с **любым** FastAPI проектом без необходимости в специфичной инфраструктуре проекта. Библиотека использует стандартные типы Python (dict, Protocol) и позволяет проектам адаптировать свою существующую инфраструктуру ошибок для работы с библиотекой через структурную типизацию.

**Ключевые принципы:**
- **Универсальность** — работает с любым FastAPI проектом
- **Прозрачность** — все документированные ошибки видны сразу в эндпоинте
- **Самодостаточность** — не нужно искать в других файлах для понимания документированных ошибок
- **Совместимость** — работает с существующей инфраструктурой проекта через Protocol

## Установка

```bash
pip install fastapi-errors-plus
```

Или установка из исходников:

```bash
git clone git@github.com:seligoroff/fastapi-errors-plus.git
cd fastapi-errors-plus
pip install -e .
```

## Быстрый старт

### Базовое использование

```python
from fastapi import APIRouter
from fastapi_errors_plus import Errors

router = APIRouter()

@router.delete(
    "/{id}",
    responses=Errors(
        {404: {                      # 404 через dict
            "description": "Not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Item not found"},
                },
            },
        }},
        unauthorized_401=True,      # 401 Unauthorized (явно)
        forbidden_403=True,          # 403 Forbidden (явно)
        # validation_error_422=True - укажите явно, если документируете 422
    ),
)
def delete_item(id: int):
    """Удалить элемент."""
    # ... ваш код ...
    pass
```

## Рекомендуемый путь

Для новых эндпоинтов предпочитайте **`ErrorDoc`** или **доменные исключения**, реализующие **`ErrorDTO`**. Используйте **`ErrorProfile`** для дефолтов проекта. **`BaseErrorDTO`** / **`StandardErrorDTO`**, флаги (`*_401`, …) и сырые OpenAPI dict можно комбинировать в одном `Errors(...)`.

### ErrorDoc

Для произвольных тел ответа (ADR: `code` / `detail` / `context`, не только строки `detail`) используйте **`ErrorDoc`**:

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
    openapi_json_extras={
        "schema": {
            "type": "object",
            "required": ["code", "detail"],
            "properties": {
                "code": {"type": "string"},
                "detail": {"type": "string"},
            },
        },
    },
)

@router.delete("/{id}", responses=Errors(permission_denied))
def delete_item(id: int):
    ...
```

**Плоский dict** в значении примера трактуется как полное **тело** ответа, если это не OpenAPI Example Object (ключи только среди `value`, `summary`, `description`, `externalValue`).

Опционально **`model=`** (Pydantic на внешнем response для `$ref`) и **`schema=`** (JSON Schema под `application/json`) избавляют от отдельного status-`dict` для типизированных тел ошибок:

```python
from fastapi_errors_plus import ErrorDoc, Errors

conflict = ErrorDoc(
    status_code=409,
    message="BusinessRule",
    model=ApplicationJsonError,  # опциональная Pydantic-модель
    schema={
        "type": "object",
        "required": ["code", "detail"],
        "properties": {
            "code": {"type": "string"},
            "detail": {"type": "string"},
        },
    },
    body={"code": "RULE_VIOLATION", "detail": "Item exists"},
)

@router.post("/items", responses=Errors(conflict, validation_error_422=False))
def create_item():
    ...
```

### Доменные исключения как ErrorDTO

Реализуйте **`ErrorDTO`** в доменных исключениях, чтобы runtime-ошибки и OpenAPI описывал одним типом:

```python
# domain/exceptions.py
from typing import Dict, Any

class DomainException(Exception):
    """Базовое исключение, реализующее протокол ErrorDTO."""
    status_code: int
    message: str

    def to_examples(self) -> Dict[str, Any]:
        return {self.message: {"value": {"detail": self.message}}}

    @classmethod
    def for_openapi(cls):
        """Экземпляр для документации OpenAPI."""
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

# В эндпоинте
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

Полный пример — [examples/domain_exceptions.py](examples/domain_exceptions.py).

### ErrorProfile

Дефолты на уровне проекта (frozen — не мутируются при вызовах эндпоинтов):

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

Явные kwargs `Errors` перекрывают профиль. Позиционные dict/DTO мержатся после стандартных статусов из профиля.

### Bundled DTO (`BaseErrorDTO`, `StandardErrorDTO`)

#### BaseErrorDTO

Простая реализация для ошибки с одним примером:

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
    """Удалить элемент."""
    pass
```

#### OpenAPI extras (`schema`) рядом с examples

Для ADR-тел (`code`, `detail`, опционально `context`) в спецификации нужен **`schema`** помимо **`examples`**. На **`BaseErrorDTO`** / **`StandardErrorDTO`** / **`ErrorDoc`** используйте **`openapi_json_extras`** (dict под `content["application/json"]` — без `example` / `examples`; examples задаёт **`to_examples()`**):

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

Пользовательские **`ErrorDTO`** могут определять **`to_openapi_json_media_type_extras()`** → `dict`; при непустом результате перекрывает **`openapi_json_extras`**. Поздний **`dict`** в **`Errors`** для того же статуса перекрывает те же ключи `application/json` (как при слиянии двух dict).

#### StandardErrorDTO

Расширенная реализация с несколькими примерами (удобно для 401, 403 и т.д.):

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
        # validation_error_422=True - укажите явно, если документируете 422
    ),
)
def delete_item(id: int):
    """Удалить элемент."""
    pass
```

Значения **`examples`** — сокращённая **`str`** (текст detail), **`dict`** OpenAPI Example Object (с **`summary`** / **`value`**) или произвольное **`dict`**-тело ответа (оборачивается в `{"value": body}`).

### Стандартные HTTP-флаги

Boolean-флаги для распространённых HTTP-статусов:

- `unauthorized_401=True` → 401 Unauthorized
- `forbidden_403=True` → 403 Forbidden
- `validation_error_422=True` → 422 Unprocessable Entity (opt-in; default is **not** to add 422)
- `internal_server_error_500=True` → 500 Internal Server Error

**Про 422:** по умолчанию `Errors()` **не** добавляет 422. Передайте `validation_error_422=True` (или `ErrorProfile(validation_error_422=True)`), если в спецификации нужен **документируемый библиотекой** validation error. Для ADR-API с доменными телами держите `validation_error_422=False` явно или через профиль.

Флаг управляет **только** записью, которую библиотека мержит в `responses=Errors(...)`. В **рантайме** FastAPI может возвращать `HTTPValidationError` при невалидных параметрах. В **схеме OpenAPI** FastAPI также добавляет свой ответ `422` с `HTTPValidationError` на роуты с валидируемыми path/query/body — **независимо от библиотеки**. `validation_error_422=False` **не** убирает эту запись из спеки. Если контракт не должен смешивать ADR-тела с FastAPI-validation в Swagger, документируйте доменные ошибки явно и считайте флаги библиотеки и auto-422 FastAPI разными вещами; при необходимости фильтруйте или кастомизируйте OpenAPI (например, постобработка `app.openapi()`).

```python
@router.get(
    "/protected",
    responses=Errors(
        unauthorized_401=True,
        forbidden_403=True,
    ),
)
def get_protected():
    """Защищённый эндпоинт."""
    pass
```

### Ошибки через dict

Стандартный формат FastAPI `responses` dict для пользовательских ошибок:

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
    """Создать элемент."""
    pass
```

### Пользовательские реализации `ErrorDTO`

Канонический протокол **`ErrorDTO`**:

```python
from typing import Protocol, Dict, Any

class ErrorDTO(Protocol):
    status_code: int
    message: str

    def to_examples(self) -> Dict[str, Any]:
        """Карта OpenAPI ``examples``: {"Key": {"value": {...}, "summary": "..."}}."""
        ...
```

Любой класс с этим протоколом (структурная типизация) работает с `Errors()`:

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
    """Получить ресурс."""
    pass
```

**Protocol** — если DTO уже есть или нужна своя логика. **`ErrorDoc` / bundled DTO** — для новых эндпоинтов или нескольких примеров на статус. Можно смешивать в одном `Errors()`.

На пользовательских DTO: **`openapi_json_extras`** или **`to_openapi_json_media_type_extras()`** для `schema` / `encoding` рядом с examples.

### Комбинирование флагов, dict и DTO

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
        # validation_error_422=True - укажите явно, если документируете 422
    ),
)
def create_item_mixed(id: int):
    """Создать элемент со смешанными типами ошибок."""
    pass
```

### Слияние examples и schema

Несколько ошибок с одним статус-кодом автоматически сливаются:

```python
@router.put(
    "/items/{id}",
    responses=Errors(
        Error1(),  # 404
        Error2(),  # 404
    ),
)
def update_item(id: int):
    """Обновить элемент."""
    pass
```

При слиянии одного статуса: **dict** побеждает в **`description`** над формулировкой стандартного флага; **message** DTO заменяет description только пока совпадает с дефолтной меткой библиотеки для кода.

В `content["application/json"]` сливаются `example` / `examples`; поздние **`dict`** могут добавить **`schema`**, **`encoding`** и т.д. Можно комбинировать **`ErrorDTO`** с **`dict`** на тот же статус только с не-example ключами:

```python
from fastapi import status

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

### Pydantic (опционально)

Pydantic **не обязателен**. Если уже используете — модели с `status_code`, `message` и `to_examples()` работают через структурную типизацию:

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

### DTO существующего проекта

Если в проекте уже есть DTO ошибок (например, `ApiErrorDTO`), они работают при реализации **`ErrorDTO`**:

```python
from dataclasses import dataclass

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

## Справочник API

### `Errors`

Основной класс для документирования ошибок в эндпоинтах FastAPI.

#### Конструктор

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

**Параметры:**
- `*errors`: Произвольные ошибки как dict или объекты ErrorDTO
- `unauthorized_401`: Добавить 401 Unauthorized. `None` = профиль/дефолт (по умолчанию не добавлять).
- `forbidden_403`: Добавить 403 Forbidden. `None` = профиль/дефолт (по умолчанию не добавлять).
- `validation_error_422`: Добавить 422 Unprocessable Entity.
  - `None` (по умолчанию): Не добавлять 422, если не включено в `ErrorProfile`
  - `False`: Явно отключить 422
  - `True`: Явно включить 422
- `internal_server_error_500`: Добавить 500 Internal Server Error. `None` = профиль/дефолт (по умолчанию не добавлять).
- `profile`: Опциональный **`ErrorProfile`** — дефолты проекта; явные kwargs перекрывают профиль.

**Поведение 422:** `validation_error_422=True` для эндпоинта с валидацией параметров/тела, если в спецификации нужен блок 422. Используйте **`ErrorProfile`** для дефолтов проекта.

**Возвращает:**
- Объект вроде `Mapping[int, …]`, подходящий для `responses` / OpenAPI FastAPI
- Передавайте экземпляр **как есть** — без вызова: `responses=Errors(...)`

#### Использование

```python
# Экземпляр — Mapping по HTTP-статусам
error_responses = Errors(unauthorized_401=True, forbidden_403=True)
documented = error_responses[401]  # deep copy — безопасно читать, не мутирует внутреннее состояние
```

**Изоляция:** входящие **dict** в responses **глубоко копируются** при добавлении; **`errors[status]`** возвращает **deep copy**, чтобы вызывающий код не портил шаблоны и состояние мержа.

**Описания:** блоки с только **`model`** (без `description`) получают дефолт из **`HTTPStatus.phrase`**, чтобы генерация OpenAPI не падала.

### `ErrorDTO`

Протокол для объектов ошибок, совместимых с библиотекой.

**Обязательные атрибуты:**
- `status_code: int` — HTTP статус-код
- `message: str` — Описание сообщения об ошибке

**Обязательные методы:**
- `to_examples() -> Dict[str, Any]` — карта OpenAPI `examples` для `application/json`

При инициализации `Errors(...)` объекты без `status_code`, `message` или вызываемого **`to_examples()`** вызывают **`TypeError`** с указанием, чего не хватает.

### `ErrorDoc`

Декларативный DTO для произвольных тел примеров и **`summary`** на пример.

**Конструктор:**
```python
from typing import Any, Dict, Optional, Union

class ErrorDoc:
    def __init__(
        self,
        status_code: int,
        message: str,
        examples: Optional[Dict[str, Union[str, Dict[str, Any]]]] = None,
        body: Optional[Dict[str, Any]] = None,
        example_key: Optional[str] = None,
        model: Any = None,
        schema: Optional[Dict[str, Any]] = None,
        openapi_json_extras: Optional[Dict[str, Any]] = None,
    ) -> None:
        ...
```

Если **`examples`** не задан, один пример строится из **`body`** или `{"detail": message}`.

### `ErrorProfile`

Frozen-дефолты стандартных HTTP-флагов на уровне проекта.

```python
from typing import Optional

class ErrorProfile:
    unauthorized_401: bool = False
    forbidden_403: bool = False
    validation_error_422: Optional[bool] = None  # None = профиль не задаёт 422
    internal_server_error_500: bool = False
```

Только **`validation_error_422`** — `Optional[bool]`: `None` значит, что профиль не включает 422 (решают kwargs эндпоинта / `Errors`). Остальные три флага по умолчанию **`False`**.

### `BaseErrorDTO`

Базовая реализация протокола ErrorDTO для удобства.

**Конструктор:**
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

**Пример:**
```python
error = BaseErrorDTO(status_code=404, message="Not found")
```

### `StandardErrorDTO`

Расширенная реализация с несколькими примерами. Наследует **`model`**, **`schema`** и **`openapi_json_extras`** от **`BaseErrorDTO`**.

**Конструктор:**
```python
from typing import Any, Dict, Optional, Union

class StandardErrorDTO(BaseErrorDTO):
    def __init__(
        self,
        status_code: int,
        message: str,
        model: Any = None,
        schema: Optional[Dict[str, Any]] = None,
        openapi_json_extras: Optional[Dict[str, Any]] = None,
        examples: Optional[Dict[str, Union[str, Dict[str, Any]]]] = None,
    ) -> None:
        ...
```

Значения **`examples`** — сокращённая **`str`** (текст detail), **`dict`** OpenAPI Example Object (с **`summary`** / **`value`**) или произвольное **`dict`**-тело ответа (оборачивается в `{"value": body}`).

**Пример:**
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

## Миграция с 0.9

Обновляетесь с **0.9.x**? См. **[CHANGELOG.md](CHANGELOG.md)** § 1.0.0 и полный гайд **[docs/migration-0.9-to-1.0.md](docs/migration-0.9-to-1.0.md)**.

### Breaking changes (кратко)

| Area | 0.9.x | 1.0 |
|------|-------|-----|
| DTO with only `to_example()` | Works + warning | **`TypeError`** при регистрации роутов — use `to_examples()` |
| `unauthorized`, `forbidden`, `validation_error`, `internal_server_error` | Deprecated, accepted | **`TypeError`** — use `*_401` / `*_403` / `*_422` / `*_500` |
| `Errors()` without 422 kwargs | Implicit 422 + warning | **No 422** |
| `LegacyErrorDTO`, `ErrorDTOLike` | Exported | **Removed** |

### Legacy kwargs (удалены)

```python
# 0.9.x
Errors(unauthorized=True, validation_error=False)

# 1.0
Errors(unauthorized_401=True, validation_error_422=False)
```

### Implicit 422 (удалён)

```python
# 0.9.x — bare Errors() documented 422
Errors()

# 1.0 — opt in
Errors(validation_error_422=True)
# or ErrorProfile(validation_error_422=True)
```

### `to_example()` (удалён) — мигрируйте первым

Переименуйте методы DTO в **`to_examples()`** до legacy kwargs. У bundled DTO больше нет `to_example()`. Аудит: `rg 'def to_example\b' --glob '*.py'`.

### Команды аудита

```bash
rg 'unauthorized=|forbidden=|validation_error=|internal_server_error=' --glob '*.py'
rg 'def to_example\b' --glob '*.py'
```

Прогоните diff OpenAPI в CI после обновления — чеклист в migration guide.

## Ограничения

Библиотека улучшает **прозрачность задокументированных** ошибок. Она **не** решает задачу поиска **всех реальных** ошибок эндпоинта — для этого нужен анализ всего кода (скрипты транзакций, `Depends`, операции с БД и т.д.).

**Что библиотека делает:**
- Улучшает прозрачность задокументированных ошибок
- Упрощает синтаксис документирования ошибок
- Делает ошибки видимыми прямо в эндпоинте

**Чего библиотека не делает:**
- Автоматически находить все реальные ошибки эндпоинта
- Анализировать код для поиска ошибок
- Гарантировать полноту списков ошибок

## Частые ловушки

- **Расхождение runtime и документации**: исключение может бросаться в рантайме, но отсутствовать в `responses=Errors(...)` — OpenAPI это само не обнаружит.
- **Исключения из `Depends()`**: auth/permission зависимости могут кидать 401/403, но без объявления в `Errors(...)` спецификация неполна.
- **Избыточная документация**: `Errors(...)` может описывать ответы, которые эндпоинт фактически не возвращает.
- **Обновление до 1.0**: голый `Errors()` больше не документирует 422 библиотеки — добавьте `validation_error_422=True` (или профиль), где в OpenAPI нужен validation error. FastAPI может по-прежнему добавлять свой `422` / `HTTPValidationError` в схему для валидируемых параметров.

## Вклад в проект

Вклад приветствуется! Присылайте Pull Request.

## Лицензия

MIT

## История изменений

Подробности — в [CHANGELOG.md](CHANGELOG.md).

