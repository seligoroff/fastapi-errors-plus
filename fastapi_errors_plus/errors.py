"""Main Errors class for documenting errors in FastAPI endpoints."""

from collections.abc import Mapping
from typing import Any, Dict, Iterator, Optional, Union

from fastapi import status

from fastapi_errors_plus.protocol import ErrorDTO


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
        unauthorized: bool = False,           # 401
        forbidden: bool = False,              # 403
        validation_error: Optional[bool] = None,        # 422 (None = use default True, False = disable, True = enable)
        internal_server_error: bool = False,  # 500
        # New parameters with explicit status codes (recommended)
        unauthorized_401: bool = False,      # 401 (explicit)
        forbidden_403: bool = False,          # 403 (explicit)
        validation_error_422: Optional[bool] = None,   # 422 (explicit, None = use default True, False = disable, True = enable)
        internal_server_error_500: bool = False,  # 500 (explicit)
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
            unauthorized_401: Add 401 Unauthorized error (explicit). Defaults to False.
            forbidden_403: Add 403 Forbidden error (explicit). Defaults to False.
            validation_error_422: Add 422 Unprocessable Entity error (explicit). 
                - None (default): Add 422 (True by default, FastAPI validates all parameters)
                - False: Explicitly disable 422
                - True: Explicitly enable 422
                FastAPI automatically validates all parameters (Path, Query, Body), so 422 is relevant
                in 95%+ of endpoints. Set to False only for endpoints without parameters.
            internal_server_error_500: Add 500 Internal Server Error (explicit). Defaults to False.
        
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
        
        # Add standard errors
        # New parameters with explicit codes have priority, but old ones still work
        if unauthorized_401 or unauthorized:
            self._add_standard_error(
                status.HTTP_401_UNAUTHORIZED,
                "Unauthorized",
                {"detail": "Unauthorized"},
            )
        if forbidden_403 or forbidden:
            self._add_standard_error(
                status.HTTP_403_FORBIDDEN,
                "Forbidden",
                {"detail": "Forbidden"},
            )
        # For validation_error: True by default (FastAPI validates all parameters)
        # Add 422 unless at least one parameter is explicitly False
        # If user sets validation_error=False, they want to disable 422 (even if validation_error_422 defaults to True)
        # If user sets validation_error_422=False, they want to disable 422 (even if validation_error defaults to True)
        # Only if both are explicitly False, we definitely don't add
        # If at least one is True (or None which defaults to True) and neither is explicitly False, add
        add_422 = True  # Default is True
        if validation_error is False or validation_error_422 is False:
            # At least one is explicitly False - don't add
            add_422 = False
        
        if add_422:
            self._add_standard_error(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Validation Error",
                {"detail": "Validation error"},
            )
        if internal_server_error_500 or internal_server_error:
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
    
    def _validate_error_dto(self, error: Any) -> None:
        """Validate that error object implements ErrorDTO protocol.
        
        Args:
            error: Object to validate
            
        Raises:
            TypeError: If object doesn't implement ErrorDTO protocol
            
        Example:
            ```python
            # Valid object
            class MyError:
                status_code = 404
                message = "Not found"
                def to_example(self): ...
            
            errors = Errors()
            errors._validate_error_dto(MyError())  # OK
            
            # Invalid object
            class BadError:
                status_code = 404
                # Missing message and to_example
            
            errors._validate_error_dto(BadError())  # Raises TypeError
            ```
        """
        required_attrs = ("status_code", "message")
        required_methods = ("to_example",)
        
        missing_attrs = [
            attr for attr in required_attrs 
            if not hasattr(error, attr)
        ]
        missing_methods = [
            method for method in required_methods 
            if not hasattr(error, method) or not callable(getattr(error, method, None))
        ]
        
        if missing_attrs or missing_methods:
            missing = missing_attrs + missing_methods
            raise TypeError(
                f"ErrorDTO object must have {', '.join(required_attrs)} attributes "
                f"and {', '.join(required_methods)}() method. "
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
    STANDARD_DESCRIPTIONS = {
        status.HTTP_401_UNAUTHORIZED: "Unauthorized",
        status.HTTP_403_FORBIDDEN: "Forbidden",
        status.HTTP_422_UNPROCESSABLE_ENTITY: "Validation Error",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "Internal Server Error",
    }
    
    def _add_standard_error(
        self,
        status_code: int,
        description: str,
        example: Dict[str, Any],
    ) -> None:
        """Add standard error.
        
        If the status code already exists, merges the example with existing examples
        using a unique key instead of overwriting.
        
        Args:
            status_code: HTTP status code (e.g., 401, 403, 422, 500)
            description: Error description for OpenAPI
            example: Example response body (e.g., {"detail": "Unauthorized"})
        """
        # Generate unique key for standard example
        standard_keys = {
            status.HTTP_401_UNAUTHORIZED: "StandardUnauthorized",
            status.HTTP_403_FORBIDDEN: "StandardForbidden",
            status.HTTP_422_UNPROCESSABLE_ENTITY: "StandardValidationError",
            status.HTTP_500_INTERNAL_SERVER_ERROR: "StandardInternalServerError",
        }
        example_key = standard_keys.get(status_code, f"Standard{status_code}")
        
        if status_code not in self._responses:
            self._responses[status_code] = {
                "description": description,
                "content": {
                    "application/json": {
                        "example": example,
                    },
                },
            }
        else:
            # If already exists, add to examples without overwriting
            # Safely access content/application/json with defaults
            existing = self._responses[status_code]
            existing_content = existing.setdefault("content", {})
            content = existing_content.setdefault("application/json", {})
            
            # Convert example to examples if needed
            if "examples" not in content:
                if "example" in content:
                    existing_example = content.pop("example")
                    content["examples"] = {
                        "default": {"value": existing_example},
                    }
                else:
                    content["examples"] = {}
            
            # Add new example with unique key (don't overwrite existing!)
            # Check if example_key already exists in examples, use unique key if needed
            unique_key = self._unique_key(content["examples"], example_key)
            content["examples"][unique_key] = {"value": example}
            
            # Don't overwrite description if it already exists
            # Priority: dict > DTO > standard flags
    
    def _add_dict_error(self, error_dict: Dict[int, Dict[str, Any]]) -> None:
        """Add error from dict in FastAPI responses format.
        
        Merges examples instead of overwriting the entire response entry.
        
        Args:
            error_dict: Dict in format {status_code: {"description": ..., "content": {...}}}
        """
        for status_code, response_data in error_dict.items():
            if status_code not in self._responses:
                # New status code - just add it
                self._responses[status_code] = response_data
            else:
                # Status code already exists - merge
                existing = self._responses[status_code]
                
                # Merge description (dict takes priority)
                if "description" in response_data:
                    existing["description"] = response_data["description"]
                
                # Merge content
                if "content" in response_data:
                    existing_content = existing.setdefault("content", {})
                    response_content = response_data["content"]
                    
                    # Merge application/json
                    if "application/json" in response_content:
                        existing_json = existing_content.setdefault("application/json", {})
                        response_json = response_content["application/json"]
                        
                        # Handle example/examples
                        if "examples" in response_json:
                            # Response has examples
                            if "examples" not in existing_json:
                                # Convert existing example to examples if needed
                                if "example" in existing_json:
                                    existing_example = existing_json.pop("example")
                                    existing_json["examples"] = {
                                        "default": {"value": existing_example},
                                    }
                                else:
                                    existing_json["examples"] = {}
                            
                            # Merge examples
                            existing_json["examples"].update(response_json["examples"])
                        elif "example" in response_json:
                            # Response has example - convert and merge
                            if "examples" not in existing_json:
                                # Convert existing example to examples if needed
                                if "example" in existing_json:
                                    existing_example = existing_json.pop("example")
                                    # Check if existing example is from a standard flag
                                    # Standard flags use specific messages
                                    standard_messages = {
                                        "Unauthorized": "StandardUnauthorized",
                                        "Forbidden": "StandardForbidden",
                                        "Validation error": "StandardValidationError",
                                        "Internal Server Error": "StandardInternalServerError",
                                    }
                                    existing_detail = existing_example.get("detail", "")
                                    example_key = standard_messages.get(existing_detail, "default")
                                    existing_json["examples"] = {
                                        example_key: {"value": existing_example},
                                    }
                                else:
                                    existing_json["examples"] = {}
                            
                            # Add new example - use "default" if available, otherwise unique key
                            if "default" not in existing_json["examples"]:
                                existing_json["examples"]["default"] = {"value": response_json["example"]}
                            else:
                                # If default exists, add with a unique key
                                unique_key = self._unique_key(existing_json["examples"], "CustomExample")
                                existing_json["examples"][unique_key] = {"value": response_json["example"]}
    
    def _add_error_dto(self, error_dto: ErrorDTO) -> None:
        """Add error from ErrorDTO (via Protocol).
        
        If the status code already exists, merges examples with existing examples.
        
        Args:
            error_dto: Error object implementing ErrorDTO protocol.
                Must have `status_code`, `message`, and `to_example()` method.
        
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
        examples = error_dto.to_example()
        
        if status_code not in self._responses:
            self._responses[status_code] = {
                "description": error_dto.message,
                "content": {
                    "application/json": {
                        "examples": examples,
                    },
                },
            }
        else:
            # Merge examples for the same status code
            # Safely access content/application/json with defaults
            existing = self._responses[status_code]
            
            # If description is standard, replace it with DTO message (priority: DTO > flags)
            if existing.get("description") == self.STANDARD_DESCRIPTIONS.get(status_code):
                existing["description"] = error_dto.message
            
            existing_content = existing.setdefault("content", {})
            content_json = existing_content.setdefault("application/json", {})
            existing_examples = content_json.get("examples", {})
            
            if "example" in content_json:
                # Convert example to examples with correct key for standard flags
                existing_example = content_json.pop("example")
                existing_detail = existing_example.get("detail", "")
                
                # Check if existing example is from a standard flag
                standard_messages = {
                    "Unauthorized": "StandardUnauthorized",
                    "Forbidden": "StandardForbidden",
                    "Validation error": "StandardValidationError",
                    "Internal Server Error": "StandardInternalServerError",
                }
                example_key = standard_messages.get(existing_detail, "default")
                
                existing_examples = {
                    example_key: {
                        "value": existing_example,
                    },
                }
            
            # Merge new examples from ErrorDTO
            existing_examples.update(examples)
            content_json["examples"] = existing_examples
    
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
        return self._responses[key]
    
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

