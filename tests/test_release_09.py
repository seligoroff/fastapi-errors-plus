"""Tests for release 0.9.0 (profile, model/schema on DTO, merge refactor, deprecations)."""

import warnings

import pytest
from fastapi import status

from fastapi_errors_plus import BaseErrorDTO, ErrorDoc, ErrorProfile, Errors


@pytest.mark.unit
class TestErrorProfile:
    def test_profile_applies_standard_flags(self):
        profile = ErrorProfile(
            unauthorized_401=True,
            validation_error_422=False,
            internal_server_error_500=True,
        )
        errors = Errors(profile=profile)
        assert 401 in errors
        assert 500 in errors
        assert status.HTTP_422_UNPROCESSABLE_CONTENT not in errors

    def test_explicit_kwargs_override_profile(self):
        profile = ErrorProfile(unauthorized_401=True, validation_error_422=False)
        errors = Errors(forbidden_403=True, profile=profile, validation_error_422=False)
        assert 401 in errors
        assert 403 in errors

    def test_profile_does_not_mutate_on_merge(self):
        profile = ErrorProfile(validation_error_422=False)
        Errors({409: {"description": "x"}}, profile=profile)
        errors2 = Errors(profile=profile)
        assert 409 not in errors2


@pytest.mark.unit
class TestDtoModelAndSchema:
    def test_error_doc_model_on_response(self):
        class M:
            pass

        doc = ErrorDoc(
            status_code=401,
            message="Unauthorized",
            model=M,
            body={"code": "UNAUTHORIZED", "detail": "bad token"},
        )
        errors = Errors(doc, validation_error_422=False)
        assert errors[401]["model"] is M

    def test_error_doc_schema_without_extra_dict(self):
        schema = {
            "type": "object",
            "properties": {"code": {"type": "string"}, "detail": {"type": "string"}},
        }
        doc = ErrorDoc(
            status_code=409,
            message="Conflict",
            schema=schema,
            body={"code": "CONFLICT", "detail": "exists"},
        )
        errors = Errors(doc, validation_error_422=False)
        aj = errors[409]["content"]["application/json"]
        assert aj["schema"] == schema
        assert "Conflict" in aj["examples"]

    def test_base_error_dto_model_merges_with_flag(self):
        class M:
            pass

        dto = BaseErrorDTO(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Token expired",
            model=M,
        )
        errors = Errors(dto, unauthorized_401=True, validation_error_422=False)
        assert errors[401]["model"] is M


@pytest.mark.unit
class TestFlagExampleKeyRegistry:
    def test_flag_then_dto_uses_standard_key_not_detail_guess(self):
        dto = BaseErrorDTO(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Custom auth message",
        )
        errors = Errors(dto, unauthorized_401=True, validation_error_422=False)
        examples = errors[401]["content"]["application/json"]["examples"]
        assert "StandardUnauthorized" in examples
        assert "Custom auth message" in examples


@pytest.mark.unit
class TestLegacyKwargsDeprecation:
    def test_legacy_unauthorized_warns(self):
        with pytest.warns(DeprecationWarning, match="unauthorized_401"):
            Errors(unauthorized=True, validation_error_422=False)

    def test_implicit_422_default_warns(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            Errors(unauthorized_401=True)
        dep = [w for w in caught if "validation_error_422" in str(w.message)]
        assert len(dep) == 1

    def test_explicit_422_false_silences_implicit_warning(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            Errors(unauthorized_401=True, validation_error_422=False)


@pytest.mark.unit
class TestProtocolValidation:
    def test_non_callable_to_example_raises_before_collect(self):
        class Bad:
            status_code = 404
            message = "x"
            to_example = "nope"

        with pytest.raises(TypeError, match="to_examples or to_example"):
            Errors(Bad(), validation_error_422=False)
