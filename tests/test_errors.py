"""Unit tests for Errors class."""

from collections.abc import Mapping

import pytest
from fastapi import status

from fastapi_errors_plus import Errors


@pytest.mark.unit
class TestErrorsStandardFlags:
    """Tests for standard HTTP status flags."""

    def test_unauthorized_401_flag(self):
        """Test generation of 401 Unauthorized from explicit flag."""
        errors = Errors(unauthorized_401=True)
        responses = errors

        assert status.HTTP_401_UNAUTHORIZED in responses
        assert responses[status.HTTP_401_UNAUTHORIZED]["description"] == "Unauthorized"

    def test_forbidden_403_flag(self):
        """Test generation of 403 Forbidden from explicit flag."""
        errors = Errors(forbidden_403=True)
        responses = errors

        assert status.HTTP_403_FORBIDDEN in responses
        assert responses[status.HTTP_403_FORBIDDEN]["description"] == "Forbidden"

    def test_validation_error_422_flag(self):
        """Test generation of 422 Validation Error from explicit flag."""
        errors = Errors(validation_error_422=True)
        responses = errors

        assert status.HTTP_422_UNPROCESSABLE_CONTENT in responses
        assert (
            responses[status.HTTP_422_UNPROCESSABLE_CONTENT]["description"]
            == "Validation Error"
        )

    def test_internal_server_error_500_flag(self):
        """Test generation of 500 Internal Server Error from explicit flag."""
        errors = Errors(internal_server_error_500=True)
        responses = errors

        assert status.HTTP_500_INTERNAL_SERVER_ERROR in responses
        assert (
            responses[status.HTTP_500_INTERNAL_SERVER_ERROR]["description"]
            == "Internal Server Error"
        )

    def test_explicit_flags_disable_422(self):
        """Explicit *_422=False disables implicit 422."""
        errors = Errors(
            unauthorized_401=True, forbidden_403=True, validation_error_422=False
        )
        responses = errors

        assert status.HTTP_401_UNAUTHORIZED in responses
        assert status.HTTP_403_FORBIDDEN in responses
        assert len(responses) == 2

    def test_multiple_flags(self):
        """Test generation of multiple standard flags."""
        errors = Errors(
            unauthorized_401=True,
            forbidden_403=True,
            validation_error_422=True,
            internal_server_error_500=True,
        )
        responses = errors

        assert status.HTTP_401_UNAUTHORIZED in responses
        assert status.HTTP_403_FORBIDDEN in responses
        assert status.HTTP_422_UNPROCESSABLE_CONTENT in responses
        assert status.HTTP_500_INTERNAL_SERVER_ERROR in responses
        assert len(responses) == 4


@pytest.mark.unit
class TestErrorsDict:
    """Tests for dict-based errors."""

    def test_single_dict_error(self):
        """Test generation of responses from single dict."""
        errors = Errors(
            {
                404: {
                    "description": "Not found",
                    "content": {
                        "application/json": {
                            "example": {"detail": "Not found"},
                        },
                    },
                },
            }
        )
        responses = errors

        assert status.HTTP_404_NOT_FOUND in responses
        assert responses[status.HTTP_404_NOT_FOUND]["description"] == "Not found"

    def test_multiple_dict_errors(self):
        """Test generation of responses from multiple dict errors."""
        errors = Errors(
            {
                404: {
                    "description": "Not found",
                    "content": {
                        "application/json": {
                            "example": {"detail": "Not found"},
                        },
                    },
                },
                409: {
                    "description": "Conflict",
                    "content": {
                        "application/json": {
                            "example": {"detail": "Conflict"},
                        },
                    },
                },
            },
            validation_error_422=False,  # Disable 422 for this test
        )
        responses = errors

        assert status.HTTP_404_NOT_FOUND in responses
        assert status.HTTP_409_CONFLICT in responses
        assert len(responses) == 2

    def test_dict_with_examples(self):
        """Test dict error with multiple examples."""
        errors = Errors(
            {
                401: {
                    "description": "Unauthorized",
                    "content": {
                        "application/json": {
                            "examples": {
                                "InvalidToken": {"value": {"detail": "Invalid token"}},
                                "SessionNotFound": {
                                    "value": {"detail": "Session not found"}
                                },
                            },
                        },
                    },
                },
            }
        )
        responses = errors

        assert status.HTTP_401_UNAUTHORIZED in responses
        examples = responses[status.HTTP_401_UNAUTHORIZED]["content"][
            "application/json"
        ]["examples"]
        assert "InvalidToken" in examples
        assert "SessionNotFound" in examples


@pytest.mark.unit
class TestErrorsErrorDTO:
    """Tests for ErrorDTO-based errors."""

    def test_single_error_dto(self, simple_error_dto):
        """Test generation of responses from single ErrorDTO."""
        error_dto = simple_error_dto(
            status_code=404, message="Not found", detail="Not found"
        )
        errors = Errors(error_dto)
        responses = errors

        assert status.HTTP_404_NOT_FOUND in responses
        assert responses[status.HTTP_404_NOT_FOUND]["description"] == "Not found"
        examples = responses[status.HTTP_404_NOT_FOUND]["content"]["application/json"][
            "examples"
        ]
        assert "Not found" in examples

    def test_multiple_error_dto_different_status(self, simple_error_dto):
        """Test generation of responses from multiple ErrorDTO with different status codes."""
        error1 = simple_error_dto(
            status_code=404, message="Not found", detail="Not found"
        )
        error2 = simple_error_dto(
            status_code=409, message="Conflict", detail="Conflict"
        )
        errors = Errors(
            error1, error2, validation_error_422=False
        )  # Disable 422 for this test
        responses = errors

        assert status.HTTP_404_NOT_FOUND in responses
        assert status.HTTP_409_CONFLICT in responses
        assert len(responses) == 2


@pytest.mark.unit
class TestErrorsMergeExamples:
    """Tests for merging examples for the same status code."""

    def test_merge_error_dto_same_status(self, simple_error_dto):
        """Test merging examples from multiple ErrorDTO with same status code."""
        error1 = simple_error_dto(status_code=404, message="Error 1", detail="Error 1")
        error2 = simple_error_dto(status_code=404, message="Error 2", detail="Error 2")
        errors = Errors(error1, error2)
        responses = errors

        assert status.HTTP_404_NOT_FOUND in responses
        examples = responses[status.HTTP_404_NOT_FOUND]["content"]["application/json"][
            "examples"
        ]
        assert len(examples) == 2
        assert "Error 1" in examples
        assert "Error 2" in examples

    def test_merge_flag_and_dict_same_status(self):
        """Test merging flag and dict for the same status code."""
        errors = Errors(
            {
                401: {
                    "description": "Unauthorized",
                    "content": {
                        "application/json": {
                            "examples": {
                                "InvalidToken": {"value": {"detail": "Invalid token"}},
                            },
                        },
                    },
                },
            },
            unauthorized_401=True,  # Also adds 401
        )
        responses = errors

        assert status.HTTP_401_UNAUTHORIZED in responses
        # Dict should take precedence (or merge)
        examples = responses[status.HTTP_401_UNAUTHORIZED]["content"][
            "application/json"
        ].get("examples", {})
        # Should have at least the dict example
        assert "InvalidToken" in examples or "default" in examples

    def test_merge_flag_and_error_dto_same_status(self, simple_error_dto):
        """Test merging flag and ErrorDTO for the same status code."""
        error_dto = simple_error_dto(
            status_code=401, message="Custom error", detail="Custom error"
        )
        errors = Errors(
            error_dto,
            unauthorized_401=True,  # Also adds 401
        )
        responses = errors

        assert status.HTTP_401_UNAUTHORIZED in responses
        # ErrorDTO examples should be merged with flag example
        content = responses[status.HTTP_401_UNAUTHORIZED]["content"]["application/json"]
        assert "examples" in content or "example" in content


@pytest.mark.unit
class TestErrorsOpenApiSchemaMerge:
    """Merging schema / non-example Media Type keys with ErrorDTO or other dict fragments."""

    def test_merge_error_dto_then_dict_adds_schema(self, simple_error_dto):
        """Examples from ErrorDTO plus OpenAPI schema from a second fragment (same status)."""
        error_dto = simple_error_dto(
            status_code=status.HTTP_404_NOT_FOUND,
            message="NotFound",
            detail="nothing",
        )
        schema_frag = {"$ref": "#/components/schemas/AppError"}
        errors = Errors(
            error_dto,
            {
                status.HTTP_404_NOT_FOUND: {
                    "content": {
                        "application/json": {
                            "schema": schema_frag,
                        },
                    },
                },
            },
            validation_error_422=False,
        )
        aj = errors[status.HTTP_404_NOT_FOUND]["content"]["application/json"]
        assert aj["schema"] == schema_frag
        assert len(aj["examples"]) >= 1
        assert "NotFound" in aj["examples"]

    def test_merge_dict_schema_then_error_dto_keeps_schema(self, simple_error_dto):
        """Schema-only fragment first; DTO merges examples without dropping schema."""
        schema_frag = {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "detail": {"type": "string"},
            },
        }
        error_dto = simple_error_dto(
            status_code=status.HTTP_404_NOT_FOUND,
            message="NotFound",
            detail="nothing",
        )
        errors = Errors(
            {
                status.HTTP_404_NOT_FOUND: {
                    "content": {"application/json": {"schema": schema_frag}},
                },
            },
            error_dto,
            validation_error_422=False,
        )
        aj = errors[status.HTTP_404_NOT_FOUND]["content"]["application/json"]
        assert aj["schema"] == schema_frag
        assert "NotFound" in aj["examples"]

    def test_later_dict_schema_overwrites_earlier(self):
        """Second dict for the same status overwrites schema (dict wins, same as description)."""
        errors = Errors(
            {
                status.HTTP_404_NOT_FOUND: {
                    "content": {"application/json": {"schema": {"type": "string"}}},
                },
            },
            {
                status.HTTP_404_NOT_FOUND: {
                    "content": {"application/json": {"schema": {"type": "object"}}},
                },
            },
            validation_error_422=False,
        )
        assert (
            errors[status.HTTP_404_NOT_FOUND]["content"]["application/json"]["schema"][
                "type"
            ]
            == "object"
        )

    def test_merge_non_example_encoding_key_from_dict(self):
        errors = Errors(
            {
                status.HTTP_404_NOT_FOUND: {
                    "content": {"application/json": {"encoding": "utf-8"}},
                },
            },
            validation_error_422=False,
        )
        assert (
            errors[status.HTTP_404_NOT_FOUND]["content"]["application/json"]["encoding"]
            == "utf-8"
        )

    def test_openapi_json_extras_without_second_fragment_dict(self):
        """ADR-style payload: schema on BaseErrorDTO, no duplicate status dict required."""
        from fastapi_errors_plus import BaseErrorDTO

        adr_schema = {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "detail": {"type": "string"},
                "context": {"type": "object"},
            },
        }
        err = BaseErrorDTO(
            status_code=status.HTTP_409_CONFLICT,
            message="BusinessRule",
            openapi_json_extras={
                "schema": adr_schema,
            },
        )
        errors = Errors(err, validation_error_422=False)
        aj = errors[status.HTTP_409_CONFLICT]["content"]["application/json"]
        assert aj["schema"] == adr_schema
        assert aj["examples"]["BusinessRule"]["value"]["detail"] == "BusinessRule"

    def test_later_dict_overwrites_schema_from_dto_openapi_json_extras(self):
        from fastapi_errors_plus import BaseErrorDTO

        dto = BaseErrorDTO(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Missing",
            openapi_json_extras={"schema": {"type": "string"}},
        )
        errors = Errors(
            dto,
            {
                status.HTTP_404_NOT_FOUND: {
                    "content": {"application/json": {"schema": {"type": "object"}}},
                },
            },
            validation_error_422=False,
        )
        schema = errors[status.HTTP_404_NOT_FOUND]["content"]["application/json"][
            "schema"
        ]
        assert schema["type"] == "object"

    def test_to_openapi_json_media_type_extras_overrides_attribute(self):
        class CustomDTO:
            status_code = status.HTTP_403_FORBIDDEN
            message = "Denied"
            openapi_json_extras = {"schema": {"type": "string"}}

            def to_examples(self):  # type: ignore[no-untyped-def]
                return {
                    self.message: {"value": {"detail": "no"}},
                }

            def to_openapi_json_media_type_extras(self):  # type: ignore[no-untyped-def]
                return {"schema": {"description": "from method"}}

        errors = Errors(CustomDTO(), validation_error_422=False)
        assert (
            errors[403]["content"]["application/json"]["schema"]["description"]
            == "from method"
        )


@pytest.mark.unit
class TestErrorsMixed:
    """Tests for mixed usage (flags + dict + ErrorDTO)."""

    def test_mixed_flags_dict_error_dto(self, simple_error_dto):
        """Test mixed usage of flags, dict, and ErrorDTO."""
        error_dto = simple_error_dto(
            status_code=404, message="Not found", detail="Not found"
        )
        errors = Errors(
            {
                409: {
                    "description": "Conflict",
                    "content": {
                        "application/json": {
                            "example": {"detail": "Conflict"},
                        },
                    },
                },
            },
            error_dto,
            unauthorized_401=True,
            forbidden_403=True,
            validation_error_422=False,  # Disable 422 for this test
        )
        responses = errors

        assert status.HTTP_401_UNAUTHORIZED in responses
        assert status.HTTP_403_FORBIDDEN in responses
        assert status.HTTP_404_NOT_FOUND in responses
        assert status.HTTP_409_CONFLICT in responses
        assert len(responses) == 4


@pytest.mark.unit
class TestErrorsEdgeCases:
    """Tests for edge cases."""

    def test_empty_errors(self):
        """Test empty Errors instance (no implicit 422)."""
        errors = Errors()
        responses = errors

        assert isinstance(responses, Mapping)
        assert status.HTTP_422_UNPROCESSABLE_CONTENT not in responses
        assert len(responses) == 0

    def test_validation_error_422_default_false(self):
        """Test that validation_error_422 is False by default."""
        errors = Errors()
        responses = errors

        assert status.HTTP_422_UNPROCESSABLE_CONTENT not in responses

    def test_validation_error_can_be_disabled(self):
        """Test that validation_error_422 can be explicitly set to False."""
        errors = Errors(validation_error_422=False)
        responses = errors

        assert status.HTTP_422_UNPROCESSABLE_CONTENT not in responses
        assert len(responses) == 0

    def test_validation_error_422_explicit_true(self):
        """Test that validation_error_422=True adds 422."""
        errors = Errors(validation_error_422=True)
        responses = errors

        assert status.HTTP_422_UNPROCESSABLE_CONTENT in responses
        assert (
            responses[status.HTTP_422_UNPROCESSABLE_CONTENT]["description"]
            == "Validation Error"
        )

    def test_validation_error_422_can_be_disabled(self):
        """Test that validation_error_422 can be explicitly set to False."""
        errors = Errors(validation_error_422=False)
        responses = errors

        assert status.HTTP_422_UNPROCESSABLE_CONTENT not in responses

    def test_validation_error_422_from_profile(self):
        """Test validation_error_422=True via ErrorProfile."""
        from fastapi_errors_plus import ErrorProfile

        errors = Errors(profile=ErrorProfile(validation_error_422=True))
        responses = errors

        assert status.HTTP_422_UNPROCESSABLE_CONTENT in responses

    def test_validation_error_with_other_errors(self):
        """Test other flags do not implicitly add 422."""
        errors = Errors(unauthorized_401=True, forbidden_403=True)
        responses = errors

        assert status.HTTP_401_UNAUTHORIZED in responses
        assert status.HTTP_403_FORBIDDEN in responses
        assert status.HTTP_422_UNPROCESSABLE_CONTENT not in responses
        assert len(responses) == 2

    def test_no_flags_no_errors(self):
        """Test Errors with all flags explicitly set to False."""
        errors = Errors(
            unauthorized_401=False,
            forbidden_403=False,
            validation_error_422=False,
            internal_server_error_500=False,
        )
        responses = errors

        assert len(responses) == 0

    def test_duplicate_dict_same_status(self):
        """Test duplicate dict entries for same status code (last wins)."""
        errors = Errors(
            {
                404: {
                    "description": "First",
                    "content": {
                        "application/json": {
                            "example": {"detail": "First"},
                        },
                    },
                },
            },
            {
                404: {
                    "description": "Second",
                    "content": {
                        "application/json": {
                            "example": {"detail": "Second"},
                        },
                    },
                },
            },
        )
        responses = errors

        assert status.HTTP_404_NOT_FOUND in responses
        # Last dict should win (dict.update behavior)
        assert responses[status.HTTP_404_NOT_FOUND]["description"] == "Second"

    def test_merge_drop_preserves_non_json_media_types_and_headers_links(self):
        """When status code collides, merge must not drop non-json content or headers/links."""
        errors = Errors(
            {
                401: {
                    "description": "First",
                    "headers": {"X-A": {"description": "a"}},
                    "links": {"L-A": {"operationId": "a"}},
                    "content": {
                        "application/problem+json": {
                            "example": {"detail": "p1"}
                        },
                        "text/plain": {"example": "t1"},
                    },
                }
            },
            {
                401: {
                    "description": "Second",
                    "headers": {"X-B": {"description": "b"}},
                    "links": {"L-B": {"operationId": "b"}},
                    "content": {
                        "application/problem+json": {
                            "example": {"detail": "p2"}
                        }
                    },
                }
            },
        )

        resp = errors[status.HTTP_401_UNAUTHORIZED]
        assert resp["description"] == "Second"

        # Non-application/json media types must be preserved (not dropped).
        assert "text/plain" in resp["content"]
        assert resp["content"]["text/plain"]["example"] == "t1"

        # application/problem+json should update from the later dict.
        assert (
            resp["content"]["application/problem+json"]["example"]["detail"] == "p2"
        )

        # Response-level headers/links should be merged (not dropped).
        assert "headers" in resp
        assert set(resp["headers"].keys()) == {"X-A", "X-B"}
        assert "links" in resp
        assert set(resp["links"].keys()) == {"L-A", "L-B"}

    def test_errors_is_mapping(self):
        """Test that Errors implements Mapping protocol."""
        errors = Errors(
            unauthorized_401=True, validation_error_422=False
        )  # Disable 422 to test only 401

        assert isinstance(errors, Mapping)
        assert 401 in errors
        assert errors[401]["description"] == "Unauthorized"
        assert len(errors) == 1


@pytest.mark.unit
class TestUniqueKeys:
    """Tests for unique key generation to prevent collisions."""

    def test_unique_keys_for_standard_errors(self):
        """Test that standard error keys are unique when merging."""
        # First add flag (creates example), then add dict with examples containing same key
        errors = Errors(
            {
                401: {  # Positional first - adds "StandardUnauthorized" to examples
                    "content": {
                        "application/json": {
                            "examples": {
                                "StandardUnauthorized": {"value": {"detail": "Custom"}},
                            },
                        },
                    },
                }
            },
            unauthorized_401=True,  # Named after positional - should use unique key
        )

        # Flag runs before positional dict: flag example becomes "default", dict keeps StandardUnauthorized
        examples = errors[401]["content"]["application/json"]["examples"]
        assert "StandardUnauthorized" in examples
        assert "default" in examples
        assert len(examples) == 2
        assert examples["StandardUnauthorized"]["value"]["detail"] == "Custom"
        assert examples["default"]["value"]["detail"] == "Unauthorized"

    def test_unique_keys_for_dict_errors(self):
        """Test that dict error keys are unique when merging."""
        errors = Errors(
            {
                401: {
                    "content": {
                        "application/json": {
                            "example": {"detail": "First"},
                        },
                    },
                }
            },
            {
                401: {
                    "content": {
                        "application/json": {
                            "example": {"detail": "Second"},
                        },
                    },
                }
            },
        )

        examples = errors[401]["content"]["application/json"]["examples"]
        assert "default" in examples
        # Second example should have unique key
        assert "CustomExample" in examples or "CustomExample_2" in examples
        assert len(examples) == 2

    def test_unique_keys_for_examples_map_collisions(self):
        """If both fragments provide examples with same key, later must not overwrite silently."""
        errors = Errors(
            {
                401: {
                    "content": {
                        "application/json": {
                            "examples": {
                                "E": {"value": {"detail": "First"}},
                            },
                        },
                    },
                }
            },
            {
                401: {
                    "content": {
                        "application/json": {
                            "examples": {
                                "E": {"value": {"detail": "Second"}},
                            },
                        },
                    },
                }
            },
        )

        examples = errors[401]["content"]["application/json"]["examples"]
        assert "E" in examples
        assert "E_2" in examples
        assert examples["E"]["value"]["detail"] == "First"
        assert examples["E_2"]["value"]["detail"] == "Second"
        assert len(examples) == 2

    def test_unique_keys_multiple_collisions(self) -> None:
        """Test unique key generation with multiple collisions."""
        from fastapi_errors_plus.merge_utils import unique_key as merge_unique_key

        examples = {
            "CustomExample": {"value": {"detail": "First"}},
            "CustomExample_2": {"value": {"detail": "Second"}},
        }

        # Add another CustomExample - should become CustomExample_3
        key = merge_unique_key(examples, "CustomExample")
        assert key == "CustomExample_3"

        examples[key] = {"value": {"detail": "Third"}}

        # Add another - should become CustomExample_4
        key = merge_unique_key(examples, "CustomExample")
        assert key == "CustomExample_4"


@pytest.mark.unit
class TestErrorsValidation:
    """Tests for ErrorDTO validation."""

    def test_valid_error_dto_passes(self, simple_error_dto):
        """Test that valid ErrorDTO passes validation."""
        error_dto = simple_error_dto(
            status_code=404, message="Not found", detail="Not found"
        )
        errors = Errors(error_dto)
        responses = errors

        assert status.HTTP_404_NOT_FOUND in responses

    def test_missing_to_examples_raises_typeerror(self):
        """Test that object without to_examples() raises TypeError."""

        class BadObject:
            status_code = 404
            message = "Test"

        with pytest.raises(TypeError) as exc_info:
            Errors(BadObject())

        assert "to_examples" in str(exc_info.value)
        assert "BadObject" in str(exc_info.value)

    def test_legacy_to_example_only_raises_typeerror(self):
        """DTO with only to_example() must raise TypeError (1.0)."""

        class LegacyOnly:
            status_code = 404
            message = "Test"

            def to_example(self):
                return {"Test": {"value": {"detail": "test"}}}

        with pytest.raises(TypeError, match="to_examples"):
            Errors(LegacyOnly(), validation_error_422=False)

    def test_missing_status_code_raises_typeerror(self):
        """Test that object without status_code raises TypeError."""

        class BadObject:
            message = "Test"

            def to_examples(self):
                return {"test": {"value": {"detail": "test"}}}

        with pytest.raises(TypeError) as exc_info:
            Errors(BadObject())

        assert "status_code" in str(exc_info.value)
        assert "BadObject" in str(exc_info.value)

    def test_missing_message_raises_typeerror(self):
        """Test that object without message raises TypeError."""

        class BadObject:
            status_code = 404

            def to_examples(self):
                return {"test": {"value": {"detail": "test"}}}

        with pytest.raises(TypeError) as exc_info:
            Errors(BadObject())

        assert "message" in str(exc_info.value)
        assert "BadObject" in str(exc_info.value)

    def test_non_callable_to_examples_raises_typeerror(self):
        """Test that non-callable to_examples raises TypeError."""

        class BadObject:
            status_code = 404
            message = "Test"
            to_examples = "not a method"

        with pytest.raises(TypeError) as exc_info:
            Errors(BadObject())

        assert "to_examples" in str(exc_info.value)
        assert "BadObject" in str(exc_info.value)

    def test_string_raises_typeerror(self):
        """Test that string raises TypeError."""
        with pytest.raises(TypeError) as exc_info:
            Errors("not a dict")

        assert "status_code" in str(exc_info.value) or "ErrorDTO" in str(exc_info.value)
        assert "str" in str(exc_info.value)

    def test_multiple_missing_attributes_reported(self):
        """Test that multiple missing attributes are reported."""

        class BadObject:
            # Missing all required attributes
            pass

        with pytest.raises(TypeError) as exc_info:
            Errors(BadObject())

        error_msg = str(exc_info.value)
        assert "status_code" in error_msg
        assert "message" in error_msg
        assert "to_examples" in error_msg
        assert "BadObject" in error_msg


@pytest.mark.unit
class TestDTODescriptionPriority:
    """Tests for DTO description priority over standard flags."""

    def test_dto_overrides_standard_description(self):
        """Test that ErrorDTO description overrides standard flag description."""
        from fastapi_errors_plus import StandardErrorDTO

        custom_401 = StandardErrorDTO(
            status_code=401,
            message="Custom Unauthorized",
            examples={"Custom": "Custom auth error"},
        )

        errors = Errors(
            custom_401,  # Positional first
            unauthorized_401=True,  # Named after - adds "Unauthorized"
        )

        # DTO should override standard description
        assert errors[401]["description"] == "Custom Unauthorized"

    def test_dto_does_not_override_custom_description(self):
        """Test that DTO does not override non-standard description."""
        from fastapi_errors_plus import StandardErrorDTO

        custom_401 = StandardErrorDTO(
            status_code=401,
            message="Another Custom",
            examples={"Custom": "Custom auth error"},
        )

        errors = Errors(
            {
                401: {  # Positional first - custom description
                    "description": "My Custom Description",
                    "content": {
                        "application/json": {
                            "example": {"detail": "Custom"},
                        },
                    },
                }
            },
            custom_401,  # DTO should not override dict description
        )

        # Dict description should be preserved (dict > DTO)
        assert errors[401]["description"] == "My Custom Description"


@pytest.mark.unit
class TestPydanticIntegration:
    """Tests for Pydantic model integration with ErrorDTO Protocol.

    These tests are optional - they will be skipped if Pydantic is not installed.
    This demonstrates that the library works with Pydantic models through structural typing,
    but Pydantic is not a required dependency.
    """

    def test_pydantic_model_as_error_dto(self):
        """Test that Pydantic models work with ErrorDTO Protocol (with proper skip)."""
        try:
            from pydantic import BaseModel, Field
            from typing import Dict, Any
        except ImportError:
            pytest.skip("Pydantic is not installed - this is expected and OK")

        class PydanticErrorDTO(BaseModel):
            """Pydantic model implementing ErrorDTO Protocol."""

            status_code: int = Field(..., ge=400, le=599)
            message: str = Field(..., min_length=1)

            def to_examples(self) -> Dict[str, Any]:
                """Generate examples for OpenAPI."""
                return {
                    self.message: {
                        "value": {"detail": self.message},
                    },
                }

        # Create instance
        error = PydanticErrorDTO(
            status_code=404,
            message="Not found",
        )

        # Use with Errors class
        errors = Errors(error, validation_error_422=False)
        responses = errors

        assert status.HTTP_404_NOT_FOUND in responses
        assert responses[status.HTTP_404_NOT_FOUND]["description"] == "Not found"

    def test_pydantic_model_with_additional_fields(self):
        """Test Pydantic model with additional fields."""
        try:
            from pydantic import BaseModel, Field
            from typing import Dict, Any, Optional
        except ImportError:
            pytest.skip("Pydantic is not installed - this is expected and OK")

        class DetailedErrorDTO(BaseModel):
            """Pydantic model for errors with additional fields."""

            status_code: int = Field(..., ge=400, le=599)
            message: str = Field(..., min_length=1)
            error_code: Optional[str] = Field(None, description="Internal error code")

            def to_examples(self) -> Dict[str, Any]:
                """Generate examples for OpenAPI."""
                example = {"detail": self.message}
                if self.error_code:
                    example["error_code"] = self.error_code

                return {
                    self.message: {
                        "value": example,
                    },
                }

        # Create instance
        error = DetailedErrorDTO(
            status_code=422,
            message="Validation failed",
            error_code="VALIDATION_ERROR",
        )

        # Use with Errors class
        errors = Errors(error, validation_error_422=False)
        responses = errors

        assert status.HTTP_422_UNPROCESSABLE_CONTENT in responses
        assert (
            responses[status.HTTP_422_UNPROCESSABLE_CONTENT]["description"]
            == "Validation failed"
        )

        # Check that error_code is in the example
        examples = responses[status.HTTP_422_UNPROCESSABLE_CONTENT]["content"][
            "application/json"
        ]["examples"]
        example_value = examples["Validation failed"]["value"]
        assert example_value["detail"] == "Validation failed"
        assert example_value["error_code"] == "VALIDATION_ERROR"
