# fastapi-errors-plus

[![PyPI version](https://badge.fury.io/py/fastapi-errors-plus.svg)](https://pypi.org/project/fastapi-errors-plus/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-41%20passed-success.svg)](https://github.com/seligoroff/fastapi-errors-plus)
[![Coverage](https://img.shields.io/badge/coverage-83%25-green.svg)](https://github.com/seligoroff/fastapi-errors-plus)

Универсальная библиотека для документирования ошибок в эндпоинтах FastAPI.

> [English version of README](README.md)

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
        unauthorized=True,           # 401 Unauthorized
        forbidden=True,               # 403 Forbidden
        validation_error=True,       # 422 Validation Error
    ),
)
def delete_item(id: int):
    """Удалить элемент."""
    # ... ваш код ...
    pass
```

## Возможности

### 1. Стандартные HTTP статусы через флаги

Используйте boolean флаги для распространённых HTTP статус-кодов:

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
    """Защищённый эндпоинт."""
    pass
```

### 2. Ошибки через dict

Используйте стандартный формат FastAPI `responses` dict для пользовательских ошибок:

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

### 3. Протокол ErrorDTO

Используйте объекты, реализующие протокол `ErrorDTO`, для совместимости с проектом:

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
    """Получить ресурс."""
    pass
```

### 4. Смешанное использование

Комбинируйте флаги, dict и ErrorDTO:

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
        unauthorized=True,  # Флаг
        forbidden=True,  # Флаг
    ),
)
def create_item_mixed(id: int):
    """Создать элемент со смешанными типами ошибок."""
    pass
```

### 5. Объединение примеров

Несколько ошибок с одним статус-кодом автоматически объединяются:

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

В OpenAPI спецификации будут оба примера под статус-кодом 404.

## Протокол ErrorDTO

Протокол `ErrorDTO` определяет интерфейс для объектов ошибок, совместимых с библиотекой:

```python
from typing import Protocol, Dict, Any

class ErrorDTO(Protocol):
    status_code: int
    message: str
    
    def to_example(self) -> Dict[str, Any]:
        """Генерирует пример для OpenAPI.
        
        Returns:
            Dict в формате: {"key": {"value": {"detail": "message"}}}
        """
        ...
```

Любой класс, реализующий этот протокол (через структурную типизацию), может использоваться с `Errors()`.

## Совместимость с существующими проектами

Если ваш проект уже имеет DTO ошибок (например, `ApiErrorDTO`), они могут работать с `fastapi-errors-plus`, если реализуют протокол `ErrorDTO`:

```python
# Ваш существующий ApiErrorDTO
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

# Работает напрямую с fastapi-errors-plus!
@router.delete(
    "/{id}",
    responses=Errors(
        ApiErrorDTO(status_code=404, message="Not found"),
    ),
)
def delete_item(id: int):
    pass
```

## Справочник API

### `Errors`

Основной класс для документирования ошибок в эндпоинтах FastAPI.

#### Конструктор

```python
Errors(
    *errors: Union[Dict[int, Dict[str, Any]], ErrorDTO],
    unauthorized: bool = False,
    forbidden: bool = False,
    validation_error: bool = False,
    internal_server_error: bool = False,
)
```

**Параметры:**
- `*errors`: Произвольные ошибки как dict или объекты ErrorDTO
- `unauthorized`: Добавить ошибку 401 Unauthorized
- `forbidden`: Добавить ошибку 403 Forbidden
- `validation_error`: Добавить ошибку 422 Unprocessable Entity
- `internal_server_error`: Добавить ошибку 500 Internal Server Error

**Возвращает:**
- Вызываемый объект, который возвращает `Dict[int, Dict[str, Any]]` в формате FastAPI responses

#### Использование

```python
# Вызовите экземпляр, чтобы получить dict responses
responses = Errors(unauthorized=True)
```

### `ErrorDTO`

Протокол для объектов ошибок, совместимых с библиотекой.

**Обязательные атрибуты:**
- `status_code: int` — HTTP статус-код
- `message: str` — Описание сообщения об ошибке

**Обязательные методы:**
- `to_example() -> Dict[str, Any]` — Генерирует пример для OpenAPI

## Примеры

### Пример 1: Стандартный FastAPI проект

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
    """Удалить элемент."""
    pass
```

### Пример 2: Проект с ErrorDTO

```python
from fastapi import APIRouter
from fastapi_errors_plus import Errors
from api.exceptions.dto import errors  # DTO ошибок вашего проекта

router = APIRouter()

@router.delete(
    "/{notificationId}",
    responses=Errors(
        unauthorized=True,
        forbidden=True,
        errors.notification_not_found_error,  # Ваш ErrorDTO
    ),
)
async def delete_notification(notification_id: int):
    """Удалить уведомление."""
    pass
```

### Пример 3: Множественные примеры для одного статуса

```python
@router.delete(
    "/{id}",
    responses=Errors(
        unauthorized=True,  # Базовый 401
        {401: {  # Переопределяем с множественными примерами
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
    """Удалить элемент."""
    pass
```

### Пример 4: Интеграция с Clean Architecture

Этот пример показывает, как использовать `fastapi-errors-plus` в FastAPI проекте с Clean Architecture:

**Domain Layer** (`domain/errors.py`):
```python
from typing import Protocol, Dict, Any

class DomainError(Protocol):
    """Протокол доменной ошибки, совместимый с ErrorDTO."""
    status_code: int
    message: str
    
    def to_example(self) -> Dict[str, Any]:
        """Генерирует пример для OpenAPI."""
        ...

class ItemNotFoundError:
    """Доменная ошибка для случая, когда элемент не найден."""
    status_code = 404
    message = "Item not found"
    
    def to_example(self) -> Dict[str, Any]:
        return {
            "ItemNotFound": {
                "value": {"detail": "Item not found"},
            },
        }

class ItemAlreadyExistsError:
    """Доменная ошибка для случая, когда элемент уже существует."""
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
    """Use case для создания элемента."""
    
    def execute(self, item_data: dict):
        # Бизнес-логика здесь
        if self._item_exists(item_data["id"]):
            raise ItemAlreadyExistsError()
        # ... создание элемента ...
        return item

class GetItemUseCase:
    """Use case для получения элемента."""
    
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
        unauthorized=True,  # Из dependency аутентификации
        forbidden=True,     # Из dependency авторизации
        validation_error=True,  # Из валидации FastAPI
        ItemAlreadyExistsError(),  # Доменная ошибка
    ),
)
async def create_item(
    item_data: dict,
    use_case: CreateItemUseCase = Depends(),
):
    """Создать новый элемент."""
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
        ItemNotFoundError(),  # Доменная ошибка
    ),
)
async def get_item(
    item_id: int,
    use_case: GetItemUseCase = Depends(),
):
    """Получить элемент по ID."""
    try:
        item = use_case.execute(item_id)
        return item
    except ItemNotFoundError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )
```

**Преимущества этого подхода:**
- Доменные ошибки переиспользуются между слоями
- Ошибки документируются прямо в эндпоинте
- Чистое разделение ответственности
- Domain layer не зависит от FastAPI
- Легко тестировать доменные ошибки независимо

## Ограничения

Библиотека улучшает **прозрачность документированных** ошибок. Она **не решает** проблему поиска **всех реальных** ошибок в эндпоинте, что требует анализа всего кодового основания (transaction scripts, зависимости `Depends`, операции с базой данных и т.д.).

**Что делает библиотека:**
- Улучшает прозрачность документированных ошибок
- Упрощает синтаксис документирования ошибок
- Делает ошибки видными сразу в эндпоинте

**Чего библиотека не делает:**
- Не находит все реальные ошибки в эндпоинте автоматически
- Не анализирует код для обнаружения ошибок
- Не гарантирует полноту списков ошибок

## Вклад в проект

Вклад приветствуется! Пожалуйста, не стесняйтесь отправлять Pull Request.

## Лицензия

MIT

## История изменений

Подробная история изменений доступна в [CHANGELOG.md](CHANGELOG.md).

