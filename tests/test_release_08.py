"""Tests for release 0.8.0 (issues #1–#3, #6, #11)."""

import pytest
from fastapi import status

from fastapi_errors_plus import BaseErrorDTO, ErrorDoc, Errors, StandardErrorDTO


@pytest.mark.unit
class TestRelease08Bugs:
    """P0 fixes: shallow copy, description merge, __getitem__ isolation."""

    def test_dict_shallow_copy_two_errors_do_not_alias(self):
        """#1: shared template dict must not alias between Errors instances."""
        inner = {
            "content": {
                "application/json": {
                    "example": {"detail": "A"},
                },
            },
        }
        shared = {status.HTTP_401_UNAUTHORIZED: inner}
        a = Errors(shared, validation_error_422=False)
        b = Errors(shared, validation_error_422=False)
        assert a[401] is not b[401]
        a[401]["content"]["application/json"]["example"]["detail"] = "mutated"
        assert b[401]["content"]["application/json"]["example"]["detail"] == "A"
        assert inner["content"]["application/json"]["example"]["detail"] == "A"

    def test_dict_model_then_dto_sets_description(self):
        """#2: DTO message fills description when dict had only model."""

        class Dto401:
            status_code = 401
            message = "Custom unauthorized message"

            def to_examples(self):
                return {
                    "Custom": {
                        "value": {"code": "UNAUTHORIZED", "detail": "token bad"},
                    },
                }

        errors = Errors(
            {401: {"model": dict}},
            Dto401(),
            validation_error_422=False,
        )
        assert errors[401]["description"] == "Custom unauthorized message"

    def test_getitem_returns_copy(self):
        """#3: mutating errors[code] must not change internal state."""
        errors = Errors(unauthorized_401=True, validation_error_422=False)
        view = errors[401]
        view["description"] = "Hacked"
        assert errors[401]["description"] == "Unauthorized"


@pytest.mark.unit
class TestRelease08ErrorDoc:
    """#6: declarative ErrorDoc with summary and custom body."""

    def test_error_doc_custom_body_and_summary(self):
        doc = ErrorDoc(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Forbidden",
            examples={
                "NoRole": {
                    "summary": "Missing role",
                    "value": {"code": "FORBIDDEN", "detail": "admin required"},
                },
            },
        )
        errors = Errors(doc, validation_error_422=False)
        ex = errors[403]["content"]["application/json"]["examples"]["NoRole"]
        assert ex["summary"] == "Missing role"
        assert ex["value"]["code"] == "FORBIDDEN"
        assert errors[403]["description"] == "Forbidden"

    def test_error_doc_default_body(self):
        doc = ErrorDoc(status_code=404, message="Not found", body={"code": "NF"})
        errors = Errors(doc, validation_error_422=False)
        assert errors[404]["content"]["application/json"]["examples"]["Not found"][
            "value"
        ] == {
            "code": "NF",
        }


@pytest.mark.unit
class TestRelease08ToExamples:
    """#11: to_examples() canonical; to_example() deprecated on bundled DTOs."""

    def test_base_error_dto_to_examples(self):
        dto = BaseErrorDTO(status_code=404, message="Missing")
        assert "Missing" in dto.to_examples()

    def test_base_error_dto_to_example_deprecated(self):
        dto = BaseErrorDTO(status_code=404, message="Missing")
        with pytest.warns(DeprecationWarning, match="to_examples"):
            dto.to_example()

    def test_standard_error_dto_summary(self):
        dto = StandardErrorDTO(
            status_code=401,
            message="Unauthorized",
            examples={
                "BadToken": {
                    "summary": "Invalid JWT",
                    "value": {"detail": "bad token"},
                },
            },
        )
        errors = Errors(dto, validation_error_422=False)
        assert (
            errors[401]["content"]["application/json"]["examples"]["BadToken"][
                "summary"
            ]
            == "Invalid JWT"
        )

    def test_errors_uses_to_examples_when_present(self):
        class OnlyToExamples:
            status_code = 409
            message = "Conflict"

            def to_examples(self):
                return {"C": {"value": {"detail": "c"}}}

        errors = Errors(OnlyToExamples(), validation_error_422=False)
        assert "C" in errors[409]["content"]["application/json"]["examples"]
