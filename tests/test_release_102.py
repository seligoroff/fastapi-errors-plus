"""Tests for release 1.0.2 hardening (DTO validation, 422, merge fail-fast)."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from fastapi_errors_plus import Errors
from tests.test_app import app


@pytest.mark.unit
class TestDtoValidationHardening:
    def test_to_examples_none_raises_typeerror(self) -> None:
        class BrokenDTO:
            status_code = 404
            message = "Not found"

            def to_examples(self):
                return None

        with pytest.raises(TypeError, match="must return dict"):
            Errors(BrokenDTO(), validation_error_422=False)

    def test_invalid_status_code_type_raises(self) -> None:
        class BrokenDTO:
            status_code = "404"
            message = "Not found"

            def to_examples(self):
                return {"Not found": {"value": {"detail": "x"}}}

        with pytest.raises(TypeError, match="status_code must be int"):
            Errors(BrokenDTO(), validation_error_422=False)

    def test_invalid_status_code_range_raises(self) -> None:
        class BrokenDTO:
            status_code = 99
            message = "Not found"

            def to_examples(self):
                return {"Not found": {"value": {"detail": "x"}}}

        with pytest.raises(ValueError, match="between 100 and 599"):
            Errors(BrokenDTO(), validation_error_422=False)

    def test_empty_message_raises(self) -> None:
        class BrokenDTO:
            status_code = 404
            message = "   "

            def to_examples(self):
                return {"x": {"value": {"detail": "x"}}}

        with pytest.raises(ValueError, match="non-empty str"):
            Errors(BrokenDTO(), validation_error_422=False)

    def test_to_examples_none_on_merge_raises_typeerror(self) -> None:
        class BrokenDTO:
            status_code = 404
            message = "Not found"

            def to_examples(self):
                return None

        with pytest.raises(TypeError, match="must return dict"):
            Errors(
                {404: {"description": "n"}},
                BrokenDTO(),
                validation_error_422=False,
            )


@pytest.mark.unit
class TestValidationError422Shape:
    def test_standard_422_example_is_array_detail(self) -> None:
        errors = Errors(validation_error_422=True)
        body = errors[status.HTTP_422_UNPROCESSABLE_CONTENT]["content"][
            "application/json"
        ]["example"]
        assert isinstance(body["detail"], list)
        assert body["detail"][0]["type"] == "missing"
        assert body["detail"][0]["loc"] == ["body", "field"]

    def test_standard_422_has_schema(self) -> None:
        errors = Errors(validation_error_422=True)
        media = errors[status.HTTP_422_UNPROCESSABLE_CONTENT]["content"][
            "application/json"
        ]
        assert "schema" in media
        assert media["schema"]["properties"]["detail"]["type"] == "array"


@pytest.mark.unit
class TestExamplesFailFast:
    def test_dict_with_non_mapping_examples_raises(self) -> None:
        with pytest.raises(TypeError, match="must be a mapping"):
            Errors(
                {
                    404: {
                        "content": {
                            "application/json": {
                                "examples": ["bad"],
                            },
                        },
                    },
                },
                validation_error_422=False,
            )


@pytest.mark.unit
class TestFlagDescriptionOrigin:
    def test_dto_does_not_override_user_dict_standard_wording(self) -> None:
        from fastapi_errors_plus import StandardErrorDTO

        dto = StandardErrorDTO(
            status_code=401,
            message="From DTO",
            examples={"Custom": "x"},
        )
        errors = Errors(
            {
                401: {
                    "description": "Unauthorized",
                    "content": {
                        "application/json": {
                            "example": {"detail": "Custom"},
                        },
                    },
                },
            },
            dto,
            validation_error_422=False,
        )
        assert errors[401]["description"] == "Unauthorized"


@pytest.mark.integration
class TestOpenAPIValidationError422:
    def test_standard_flags_422_in_openapi_matches_library_shape(self) -> None:
        client = TestClient(app)
        schema = client.get("/openapi.json").json()
        endpoint = schema["paths"]["/api/v1/standard-flags"]["get"]
        media = endpoint["responses"]["422"]["content"]["application/json"]
        example = media.get("example") or next(
            iter(media.get("examples", {}).values())
        )["value"]
        assert isinstance(example["detail"], list)
        assert "schema" in media
