"""Main Errors class for documenting errors in FastAPI endpoints."""

import copy
import warnings
from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, Dict, Iterator, Optional, Union

from fastapi import status

from fastapi_errors_plus.error_profile import ErrorProfile
from fastapi_errors_plus.merge_utils import (
    ensure_examples_dict,
    merge_examples_map,
    merge_singular_example,
    standard_flag_example_key,
)
from fastapi_errors_plus.protocol import ErrorDTO, LegacyErrorDTO

# Starlette (via FastAPI) prefers HTTP_422_UNPROCESSABLE_CONTENT over ENTITY.
# Older pins may lack CONTENT (import crash); avoid nested getattr(, default=)
# touching ENTITY when CONTENT exists (DeprecationWarning).
_HTTP_422: int
_http_422_attr = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", None)
if _http_422_attr is None:
    _HTTP_422 = int(getattr(status, "HTTP_422_UNPROCESSABLE_ENTITY", 422))
else:
    _HTTP_422 = int(_http_422_attr)

# OpenAPI Media Type: merge example/examples separately; other keys (schema, encoding, …) from an extra dict win.
_OPENAPI_MEDIA_TYPE_EXAMPLE_KEYS = frozenset({"example", "examples"})


def _merge_openapi_application_json_non_example(
    existing_json: Dict[str, Any],
    response_json: Dict[str, Any],
) -> None:
    """Apply schema/encoding/extra fields from incoming media type; incoming overwrites on conflict."""
    for key, value in response_json.items():
        if key not in _OPENAPI_MEDIA_TYPE_EXAMPLE_KEYS:
            existing_json[key] = value


def _pick_error_dto_application_json_extra(error_dto: Any) -> Optional[Dict[str, Any]]:
    """Optional OpenAPI ``application/json`` keys from DTO (e.g. ``schema``, ``encoding``).

    Prefer ``to_openapi_json_media_type_extras()`` when present and returns a truthy mapping;
    otherwise ``schema`` field, then ``openapi_json_extras``. Must not rely on ``example`` /
    ``examples`` here — ``to_examples()`` covers those."""
    extras: Dict[str, Any] = {}
    schema = getattr(error_dto, "schema", None)
    if isinstance(schema, dict) and schema:
        extras["schema"] = schema
    attr_extra = getattr(error_dto, "openapi_json_extras", None)
    if isinstance(attr_extra, dict) and attr_extra:
        extras.update(attr_extra)
    getter = getattr(error_dto, "to_openapi_json_media_type_extras", None)
    if callable(getter):
        out = getter()
        if isinstance(out, dict) and out:
            extras.update(out)
    return extras or None


def _pick_error_dto_model(error_dto: Any) -> Any:
    """Optional FastAPI ``model`` on the outer response object."""
    return getattr(error_dto, "model", None)


def _example_defining_class(cls: type, method: str) -> Optional[type]:
    """First class in MRO that defines *method* in its own ``__dict__``."""
    for base in cls.__mro__:
        if method in base.__dict__:
            return base
    return None


def _collect_dto_examples(error_dto: Any) -> Dict[str, Any]:
    """Return a deep copy of examples from an ErrorDTO.

      Resolution walks the MRO: the most specific ``to_examples`` wins over an
    inherited ``to_example`` on the same branch; legacy ``to_example`` only on
    the defining class emits a single actionable deprecation warning.
    """
    cls = type(error_dto)
    examples_cls = _example_defining_class(cls, "to_examples")
    legacy_cls = _example_defining_class(cls, "to_example")

    if examples_cls is not None:
        use_examples = legacy_cls is None or cls.__mro__.index(
            examples_cls
        ) <= cls.__mro__.index(legacy_cls)
        if use_examples:
            return copy.deepcopy(error_dto.to_examples())

    if legacy_cls is not None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = error_dto.to_example()
        warnings.warn(
            f"{cls.__name__} implements deprecated to_example(); use to_examples() instead.",
            DeprecationWarning,
            stacklevel=3,
        )
        return copy.deepcopy(result)

    raise TypeError(f"{cls.__name__} has no to_examples() or to_example()")


def _apply_dto_description(
    existing: Dict[str, Any],
    error_dto: Any,
    standard_descriptions: Dict[int, str],
) -> None:
    """Set ``description`` from DTO when missing, empty, or still a standard flag label."""
    desc = existing.get("description")
    if desc is None or (isinstance(desc, str) and not desc.strip()):
        existing["description"] = error_dto.message
    elif desc == standard_descriptions.get(error_dto.status_code):
        existing["description"] = error_dto.message


def _ensure_response_descriptions(responses: Dict[int, Dict[str, Any]]) -> None:
    """Fill missing descriptions so FastAPI OpenAPI generation does not assert."""
    for code, response in responses.items():
        desc = response.get("description")
        if desc is not None and isinstance(desc, str) and desc.strip():
            continue
        try:
            response["description"] = HTTPStatus(code).phrase
        except ValueError:
            response["description"] = f"HTTP {code}"


class Errors(Mapping):
    """Universal class for documenting errors in FastAPI endpoints.

    Works with any FastAPI project. Can accept:
    - Standard HTTP statuses via boolean flags
    - Dict in FastAPI responses format
    - Objects implementing ErrorDTO protocol (for project compatibility)

    Implements Mapping protocol, so can be used directly in FastAPI responses
    parameter without calling ().

    Example:
        ```python
        from fastapi import APIRouter
        from fastapi_errors_plus import Errors

        router = APIRouter()

        @router.delete(
            "/{id}",
            responses=Errors(
                {404: {                      # 404 via dict (positional first)
                    "description": "Not found",
                    "content": {
                        "application/json": {
                            "example": {"detail": "Item not found"},
                        },
                    },
                }},
                unauthorized_401=True,      # 401 (explicit, named after positional)
                forbidden_403=True,          # 403 (explicit)
                # validation_error_422=True - not needed, defaults to True
            ),
        )
        def delete_item(id: int):
            pass
        ```
    """

    def __init__(
        self,
        # Arbitrary errors (dict or ErrorDTO) - must come first
        *errors: Union[Dict[int, Dict[str, Any]], ErrorDTO],
        # Standard HTTP statuses (boolean flags)
        # Old parameters (for backward compatibility)
        unauthorized: bool = False,  # 401
        forbidden: bool = False,  # 403
        validation_error: Optional[
            bool
        ] = None,  # 422 (None = use default True, False = disable, True = enable)
        internal_server_error: bool = False,  # 500
        # New parameters with explicit status codes (recommended)
        unauthorized_401: Optional[bool] = None,  # 401 (explicit)
        forbidden_403: Optional[bool] = None,  # 403 (explicit)
        validation_error_422: Optional[
            bool
        ] = None,  # 422 (explicit, None = use default True, False = disable, True = enable)
        internal_server_error_500: Optional[bool] = None,  # 500 (explicit)
        profile: Optional[ErrorProfile] = None,
    ) -> None:
        """Initialize Errors instance.

        Args:
            *errors: Arbitrary errors as dict or ErrorDTO objects.
                Dict should be in FastAPI responses format: {status_code: {...}}.
                ErrorDTO objects must implement the ErrorDTO protocol.
            unauthorized: Add 401 Unauthorized error. Defaults to False.
                Deprecated: Use `unauthorized_401` instead for explicit status code.
            forbidden: Add 403 Forbidden error. Defaults to False.
                Deprecated: Use `forbidden_403` instead for explicit status code.
            validation_error: Add 422 Unprocessable Entity error.
                - None (default): Add 422 (True by default, FastAPI validates all parameters)
                - False: Explicitly disable 422
                - True: Explicitly enable 422
                FastAPI automatically validates all parameters (Path, Query, Body), so 422 is relevant
                in 95%+ of endpoints. Set to False only for endpoints without parameters.
                Deprecated: Use `validation_error_422` instead for explicit status code.
            internal_server_error: Add 500 Internal Server Error. Defaults to False.
                Deprecated: Use `internal_server_error_500` instead for explicit status code.
            unauthorized_401: Add 401 Unauthorized error (explicit). None means "use profile/default".
            forbidden_403: Add 403 Forbidden error (explicit). None means "use profile/default".
            validation_error_422: Add 422 Unprocessable Entity error (explicit).
                - None (default): Add 422 (True by default, FastAPI validates all parameters)
                - False: Explicitly disable 422
                - True: Explicitly enable 422
                FastAPI automatically validates all parameters (Path, Query, Body), so 422 is relevant
                in 95%+ of endpoints. Set to False only for endpoints without parameters.
            internal_server_error_500: Add 500 Internal Server Error (explicit). None means "use profile/default".

        Example:
            ```python
            # Standard flags only
            errors = Errors(unauthorized=True, forbidden=True)

            # Dict errors
            errors = Errors({404: {"description": "Not found", ...}})

            # ErrorDTO
            errors = Errors(MyErrorDTO())

            # Mixed
            errors = Errors(
                {409: {...}},
                MyErrorDTO(),
                unauthorized=True,
            )
            ```
        """
        self._responses: Dict[int, Dict[str, Any]] = {}
        self._flag_example_keys: Dict[int, str] = {}

        if unauthorized:
            warnings.warn(
                "unauthorized is deprecated; use unauthorized_401 instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        if forbidden:
            warnings.warn(
                "forbidden is deprecated; use forbidden_403 instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        if validation_error is not None:
            warnings.warn(
                "validation_error is deprecated; use validation_error_422 instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        if internal_server_error:
            warnings.warn(
                "internal_server_error is deprecated; use internal_server_error_500 instead.",
                DeprecationWarning,
                stacklevel=2,
            )

        if unauthorized_401 is not None:
            use_unauthorized = unauthorized_401
        elif unauthorized:
            use_unauthorized = True
        elif profile is not None:
            use_unauthorized = profile.unauthorized_401
        else:
            use_unauthorized = False

        if forbidden_403 is not None:
            use_forbidden = forbidden_403
        elif forbidden:
            use_forbidden = True
        elif profile is not None:
            use_forbidden = profile.forbidden_403
        else:
            use_forbidden = False

        if internal_server_error_500 is not None:
            use_internal = internal_server_error_500
        elif internal_server_error:
            use_internal = True
        elif profile is not None:
            use_internal = profile.internal_server_error_500
        else:
            use_internal = False

        val_422: Optional[bool]
        if validation_error_422 is not None:
            val_422 = validation_error_422
        elif validation_error is not None:
            val_422 = validation_error
        elif profile is not None:
            val_422 = profile.validation_error_422
        else:
            val_422 = None

        # Add standard errors
        if use_unauthorized:
            self._add_standard_error(
                status.HTTP_401_UNAUTHORIZED,
                "Unauthorized",
                {"detail": "Unauthorized"},
            )
        if use_forbidden:
            self._add_standard_error(
                status.HTTP_403_FORBIDDEN,
                "Forbidden",
                {"detail": "Forbidden"},
            )
        add_422 = True
        if val_422 is False:
            add_422 = False
        elif val_422 is None:
            add_422 = True
            warnings.warn(
                "Implicit validation_error_422=True is deprecated and will default to "
                "False in 1.0. Pass validation_error_422=False explicitly to silence.",
                DeprecationWarning,
                stacklevel=2,
            )

        if add_422:
            self._add_standard_error(
                _HTTP_422,
                "Validation Error",
                {"detail": "Validation error"},
            )
        if use_internal:
            self._add_standard_error(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Internal Server Error",
                {"detail": "Internal Server Error"},
            )

        # Add arbitrary errors
        for error in errors:
            if isinstance(error, dict):
                # Universal dict in FastAPI format - merge instead of overwrite
                self._add_dict_error(error)
            else:
                # Validate ErrorDTO protocol before processing
                self._validate_error_dto(error)
                # ErrorDTO (compatible with ApiErrorDTO via Protocol)
                self._add_error_dto(error)

        _ensure_response_descriptions(self._responses)

    def _validate_error_dto(self, error: Any) -> None:
        """Validate that error object implements ErrorDTO or LegacyErrorDTO protocol."""
        has_to_examples = callable(getattr(error, "to_examples", None))
        has_to_example = callable(getattr(error, "to_example", None))

        if isinstance(error, ErrorDTO) and has_to_examples:
            return
        if isinstance(error, LegacyErrorDTO) and has_to_example:
            return

        required_attrs = ("status_code", "message")
        missing_attrs = [attr for attr in required_attrs if not hasattr(error, attr)]
        if not has_to_examples and not has_to_example:
            missing_methods = ["to_examples or to_example"]
        else:
            missing_methods = []

        if missing_attrs or missing_methods:
            missing = missing_attrs + missing_methods
            raise TypeError(
                f"ErrorDTO object must have {', '.join(required_attrs)} attributes "
                f"and to_examples() or to_example() method. "
                f"Missing: {', '.join(missing)}. "
                f"Got {type(error).__name__}"
            )

    def _unique_key(self, examples: Dict[str, Any], base: str) -> str:
        """Generate unique key for examples dict.

        Args:
            examples: Existing examples dict
            base: Base key name

        Returns:
            Unique key that doesn't exist in examples

        Example:
            >>> errors = Errors()
            >>> errors._unique_key({"default": {}}, "default")
            "default_2"
            >>> errors._unique_key({"default": {}, "default_2": {}}, "default")
            "default_3"
        """
        key = base
        i = 2
        while key in examples:
            key = f"{base}_{i}"
            i += 1
        return key

    # Standard descriptions for priority checking
    STANDARD_DESCRIPTIONS: Dict[int, str] = {
        status.HTTP_401_UNAUTHORIZED: "Unauthorized",
        status.HTTP_403_FORBIDDEN: "Forbidden",
        _HTTP_422: "Validation Error",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "Internal Server Error",
    }

    def _prior_singular_example_key(self, status_code: int) -> Optional[str]:
        """Example-map key for a singular ``example`` from a standard flag, if any."""
        return self._flag_example_keys.get(status_code)

    def _add_standard_error(
        self,
        status_code: int,
        description: str,
        example: Dict[str, Any],
    ) -> None:
        """Add standard error.

        If the status code already exists, merges the example with existing examples
        using a unique key instead of overwriting.
        """
        example_key = standard_flag_example_key(status_code)

        if status_code not in self._responses:
            self._flag_example_keys[status_code] = example_key
            self._responses[status_code] = {
                "description": description,
                "content": {
                    "application/json": {
                        "example": example,
                    },
                },
            }
        else:
            existing = self._responses[status_code]
            existing_content = existing.setdefault("content", {})
            content = existing_content.setdefault("application/json", {})
            prior_key = self._prior_singular_example_key(status_code)
            examples = ensure_examples_dict(content, prior_singular_key=prior_key)
            unique_key = self._unique_key(examples, example_key)
            examples[unique_key] = {"value": example}

    def _add_dict_error(self, error_dict: Dict[int, Dict[str, Any]]) -> None:
        """Add error from dict in FastAPI responses format.

        Merges examples instead of overwriting the entire response entry.

        Args:
            error_dict: Dict in format {status_code: {"description": ..., "content": {...}}}
        """
        for status_code, response_data in error_dict.items():
            response_data = copy.deepcopy(response_data)
            if status_code not in self._responses:
                # New status code - deep copy so caller dict is not aliased
                self._responses[status_code] = response_data
            else:
                # Status code already exists - merge
                existing = self._responses[status_code]

                # Merge description (dict takes priority)
                if "description" in response_data:
                    existing["description"] = response_data["description"]

                # FastAPI-style shorthand on the response object (incoming dict wins)
                if "model" in response_data:
                    existing["model"] = response_data["model"]

                # Merge response-level metadata (headers/links).
                # Keep existing keys and update with incoming keys (later-wins per key).
                for key in ("headers", "links"):
                    if key not in response_data:
                        continue
                    incoming_val = response_data[key]
                    if key not in existing or not isinstance(existing.get(key), dict):
                        existing[key] = copy.deepcopy(incoming_val)
                    elif isinstance(incoming_val, dict):
                        existing[key].update(copy.deepcopy(incoming_val))
                    else:
                        # Non-dict values: later-wins fallback.
                        existing[key] = copy.deepcopy(incoming_val)

                # Merge content
                if "content" in response_data:
                    existing_content = existing.setdefault("content", {})
                    response_content = response_data["content"]

                    # application/json is special: its non-example keys and examples are merged.
                    # Other media types are later-wins, but we must not drop any existing media types.
                    for media_type, media_obj in response_content.items():
                        if media_type != "application/json":
                            existing_content[media_type] = copy.deepcopy(media_obj)
                            continue

                        existing_json = existing_content.setdefault("application/json", {})
                        response_json = media_obj

                        _merge_openapi_application_json_non_example(
                            existing_json, response_json
                        )

                        # Handle example/examples (accumulate under examples).
                        if "examples" in response_json:
                            prior_key = self._prior_singular_example_key(status_code)
                            incoming_examples = response_json["examples"]
                            if prior_key and isinstance(incoming_examples, dict) and prior_key in incoming_examples:
                                prior_key = "default"
                            merge_examples_map(
                                existing_json,
                                copy.deepcopy(incoming_examples),
                                prior_singular_key=prior_key,
                                unique_key_fn=self._unique_key,
                            )
                        elif "example" in response_json:
                            merge_singular_example(
                                existing_json,
                                response_json["example"],
                                prior_singular_key=self._prior_singular_example_key(
                                    status_code
                                ),
                                unique_key_fn=self._unique_key,
                            )

    def _add_error_dto(self, error_dto: ErrorDTO) -> None:
        """Add error from ErrorDTO (via Protocol).

        If the status code already exists, merges examples with existing examples.

        Args:
            error_dto: Object with ``status_code``, ``message``, and
                ``to_examples()`` and/or legacy ``to_example()``.

        Example:
            ```python
            class MyError:
                status_code = 404
                message = "Not found"
                def to_example(self):
                    return {"Not found": {"value": {"detail": "Not found"}}}

            errors = Errors()
            errors._add_error_dto(MyError())
            ```
        """
        status_code = error_dto.status_code
        examples = _collect_dto_examples(error_dto)
        dto_extras = _pick_error_dto_application_json_extra(error_dto)
        if dto_extras is not None:
            dto_extras = copy.deepcopy(dto_extras)
        dto_model = _pick_error_dto_model(error_dto)

        if status_code not in self._responses:
            application_json: Dict[str, Any] = {"examples": examples}
            if dto_extras is not None:
                _merge_openapi_application_json_non_example(
                    application_json, dto_extras
                )
            response_block: Dict[str, Any] = {
                "description": error_dto.message,
                "content": {
                    "application/json": application_json,
                },
            }
            if dto_model is not None:
                response_block["model"] = dto_model
            self._responses[status_code] = response_block
        else:
            existing = self._responses[status_code]

            _apply_dto_description(existing, error_dto, self.STANDARD_DESCRIPTIONS)

            if dto_model is not None:
                existing["model"] = dto_model

            existing_content = existing.setdefault("content", {})
            content_json = existing_content.setdefault("application/json", {})
            prior_key = self._prior_singular_example_key(status_code)
            merge_examples_map(
                content_json,
                copy.deepcopy(examples),
                prior_singular_key=prior_key,
                unique_key_fn=self._unique_key,
            )

            if dto_extras is not None:
                _merge_openapi_application_json_non_example(content_json, dto_extras)

    # Mapping protocol implementation
    def __getitem__(self, key: int) -> Dict[str, Any]:
        """Get response for status code.

        Args:
            key: HTTP status code (e.g., 401, 403, 404)

        Returns:
            Response dict in FastAPI format

        Raises:
            KeyError: If status code not found
        """
        return copy.deepcopy(self._responses[key])

    def __iter__(self) -> Iterator[int]:
        """Iterate over status codes.

        Returns:
            Iterator over status codes
        """
        return iter(self._responses)

    def __len__(self) -> int:
        """Get number of status codes.

        Returns:
            Number of documented error status codes
        """
        return len(self._responses)
