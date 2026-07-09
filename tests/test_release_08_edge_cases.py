"""Additional tests for release 0.8.0 (protocol, example normalization, descriptions)."""

import importlib

import pytest
from fastapi import status

from fastapi_errors_plus import BaseErrorDTO, ErrorDoc, Errors
from fastapi_errors_plus.example_utils import _normalize_example_specs
from fastapi_errors_plus.protocol import ErrorDTO


@pytest.fixture
def _reload_errors_module():
    """Reload errors module after tests that patch starlette status constants."""
    yield
    import fastapi_errors_plus.errors as errors_mod

    importlib.reload(errors_mod)


@pytest.mark.unit
class TestExampleNormalizationHeuristic:
    def test_body_with_value_field_wrapped_as_body(self):
        body = {"value": 150, "code": "LIMIT_EXCEEDED", "detail": "too high"}
        normalized = _normalize_example_specs({"bad": body})
        assert normalized["bad"] == {"value": body}

    def test_openapi_example_object_preserved(self):
        spec = {
            "summary": "Limit",
            "value": {"code": "LIMIT_EXCEEDED", "detail": "too high"},
        }
        normalized = _normalize_example_specs({"bad": spec})
        assert normalized["bad"] == spec

    def test_empty_dict_spec_wrapped_as_body(self):
        normalized = _normalize_example_specs({"empty": {}})
        assert normalized["empty"] == {"value": {}}

    def test_invalid_spec_type_raises_typeerror(self):
        with pytest.raises(TypeError, match="must be str or dict"):
            _normalize_example_specs({"bad": 42})

    def test_error_doc_domain_body_with_value_key(self):
        doc = ErrorDoc(
            status_code=422,
            message="Validation failed",
            examples={"bad": {"value": 150, "code": "LIMIT_EXCEEDED", "detail": "x"}},
        )
        errors = Errors(doc, validation_error_422=False)
        ex = errors[422]["content"]["application/json"]["examples"]["bad"]
        assert ex["value"] == {"value": 150, "code": "LIMIT_EXCEEDED", "detail": "x"}


@pytest.mark.unit
class TestResponseDescriptions:
    def test_model_only_dict_gets_http_phrase_description(self):
        errors = Errors({401: {"model": dict}}, validation_error_422=False)
        assert errors[401]["description"] == "Unauthorized"

    def test_unknown_status_code_gets_fallback_description(self):
        errors = Errors({999: {"model": dict}}, validation_error_422=False)
        assert errors[999]["description"] == "HTTP 999"


@pytest.mark.unit
class TestStandardFlagMerge:
    def test_flag_merges_when_existing_has_singular_example(self):
        errors = Errors(
            {
                401: {
                    "content": {
                        "application/json": {
                            "example": {"detail": "Custom"},
                        },
                    },
                },
            },
            unauthorized_401=True,
            validation_error_422=False,
        )
        examples = errors[401]["content"]["application/json"]["examples"]
        assert examples["default"]["value"]["detail"] == "Custom"
        assert any(
            ex["value"]["detail"] == "Unauthorized"
            for ex in examples.values()
        )


@pytest.mark.unit
class TestDtoMergeOnExistingResponse:
    def test_dto_extras_merge_after_standard_flag(self):
        dto = BaseErrorDTO(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Token expired",
            openapi_json_extras={"schema": {"type": "object"}},
        )
        errors = Errors(dto, unauthorized_401=True, validation_error_422=False)
        aj = errors[401]["content"]["application/json"]
        assert aj["schema"] == {"type": "object"}
        assert "StandardUnauthorized" in aj["examples"]
        assert "Token expired" in aj["examples"]

    def test_dto_converts_standard_flag_example_key(self):
        dto = BaseErrorDTO(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Role missing",
        )
        errors = Errors(dto, forbidden_403=True, validation_error_422=False)
        examples = errors[403]["content"]["application/json"]["examples"]
        assert "StandardForbidden" in examples
        assert "Role missing" in examples


@pytest.mark.unit
class TestDictMergeBranches:
    def test_incoming_example_merges_into_schema_only_slot(self):
        errors = Errors(
            {
                404: {
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"},
                        },
                    },
                },
            },
            {
                404: {
                    "content": {
                        "application/json": {
                            "example": {"detail": "Missing"},
                        },
                    },
                },
            },
            validation_error_422=False,
        )
        aj = errors[404]["content"]["application/json"]
        assert aj["schema"] == {"type": "object"}
        assert aj["examples"]["default"]["value"]["detail"] == "Missing"

    def test_second_example_gets_unique_key_when_default_taken(self):
        errors = Errors(
            {
                409: {
                    "content": {
                        "application/json": {
                            "example": {"detail": "First"},
                        },
                    },
                },
            },
            {
                409: {
                    "content": {
                        "application/json": {
                            "example": {"detail": "Second"},
                        },
                    },
                },
            },
            validation_error_422=False,
        )
        examples = errors[409]["content"]["application/json"]["examples"]
        assert examples["default"]["value"]["detail"] == "First"
        assert any(
            ex["value"]["detail"] == "Second"
            for key, ex in examples.items()
            if key != "default"
        )


@pytest.mark.unit
class TestHttp422ImportFallback:
    def test_http_422_falls_back_when_content_constant_missing(
        self, monkeypatch, _reload_errors_module
    ):
        from starlette import status as starlette_status

        import fastapi_errors_plus.errors as errors_mod

        monkeypatch.delattr(
            starlette_status, "HTTP_422_UNPROCESSABLE_CONTENT", raising=False
        )
        importlib.reload(errors_mod)
        expected = int(
            getattr(starlette_status, "HTTP_422_UNPROCESSABLE_ENTITY", 422)
        )
        assert errors_mod._HTTP_422 == expected


@pytest.mark.unit
class TestErrorDTOProtocols:
    def test_to_examples_satisfies_error_dto(self):
        class Modern:
            status_code = 404
            message = "Not found"

            def to_examples(self):
                return {"n": {"value": {"detail": "x"}}}

        assert isinstance(Modern(), ErrorDTO)

    def test_to_example_only_does_not_satisfy_error_dto(self):
        class Legacy:
            status_code = 404
            message = "Not found"

            def to_example(self):
                return {"n": {"value": {"detail": "x"}}}

        assert not isinstance(Legacy(), ErrorDTO)


@pytest.mark.unit
class TestLegacyToExampleRemoved:
    def test_errors_rejects_legacy_to_example_only_dto(self):
        class LegacyOnly:
            status_code = 409
            message = "Conflict"

            def to_example(self):
                return {"C": {"value": {"detail": "c"}}}

        with pytest.raises(TypeError, match="to_examples"):
            Errors(LegacyOnly(), validation_error_422=False)
