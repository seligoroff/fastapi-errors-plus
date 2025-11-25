"""Unit tests for Errors class."""

from collections.abc import Mapping

import pytest
from fastapi import status

from fastapi_errors_plus import Errors
from tests.conftest import SimpleErrorDTO


class TestErrorsStandardFlags:
    """Tests for standard HTTP status flags."""
    
    def test_unauthorized_flag(self):
        """Test generation of 401 Unauthorized from flag."""
        errors = Errors(unauthorized=True)
        responses = errors
        
        assert status.HTTP_401_UNAUTHORIZED in responses
        assert responses[status.HTTP_401_UNAUTHORIZED]["description"] == "Unauthorized"
        assert responses[status.HTTP_401_UNAUTHORIZED]["content"]["application/json"]["example"] == {
            "detail": "Unauthorized"
        }
    
    def test_forbidden_flag(self):
        """Test generation of 403 Forbidden from flag."""
        errors = Errors(forbidden=True)
        responses = errors
        
        assert status.HTTP_403_FORBIDDEN in responses
        assert responses[status.HTTP_403_FORBIDDEN]["description"] == "Forbidden"
    
    def test_validation_error_flag(self):
        """Test generation of 422 Validation Error from flag."""
        errors = Errors(validation_error=True)
        responses = errors
        
        assert status.HTTP_422_UNPROCESSABLE_ENTITY in responses
        assert responses[status.HTTP_422_UNPROCESSABLE_ENTITY]["description"] == "Validation Error"
    
    def test_internal_server_error_flag(self):
        """Test generation of 500 Internal Server Error from flag."""
        errors = Errors(internal_server_error=True)
        responses = errors
        
        assert status.HTTP_500_INTERNAL_SERVER_ERROR in responses
        assert responses[status.HTTP_500_INTERNAL_SERVER_ERROR]["description"] == "Internal Server Error"
    
    def test_multiple_flags(self):
        """Test generation of multiple standard flags."""
        errors = Errors(
            unauthorized=True,
            forbidden=True,
            validation_error=True,
            internal_server_error=True,
        )
        responses = errors
        
        assert status.HTTP_401_UNAUTHORIZED in responses
        assert status.HTTP_403_FORBIDDEN in responses
        assert status.HTTP_422_UNPROCESSABLE_ENTITY in responses
        assert status.HTTP_500_INTERNAL_SERVER_ERROR in responses
        assert len(responses) == 4


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
            }
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
                                "SessionNotFound": {"value": {"detail": "Session not found"}},
                            },
                        },
                    },
                },
            }
        )
        responses = errors
        
        assert status.HTTP_401_UNAUTHORIZED in responses
        examples = responses[status.HTTP_401_UNAUTHORIZED]["content"]["application/json"]["examples"]
        assert "InvalidToken" in examples
        assert "SessionNotFound" in examples


class TestErrorsErrorDTO:
    """Tests for ErrorDTO-based errors."""
    
    def test_single_error_dto(self, simple_error_dto):
        """Test generation of responses from single ErrorDTO."""
        error_dto = simple_error_dto(status_code=404, message="Not found", detail="Not found")
        errors = Errors(error_dto)
        responses = errors
        
        assert status.HTTP_404_NOT_FOUND in responses
        assert responses[status.HTTP_404_NOT_FOUND]["description"] == "Not found"
        examples = responses[status.HTTP_404_NOT_FOUND]["content"]["application/json"]["examples"]
        assert "Not found" in examples
    
    def test_multiple_error_dto_different_status(self, simple_error_dto):
        """Test generation of responses from multiple ErrorDTO with different status codes."""
        error1 = simple_error_dto(status_code=404, message="Not found", detail="Not found")
        error2 = simple_error_dto(status_code=409, message="Conflict", detail="Conflict")
        errors = Errors(error1, error2)
        responses = errors
        
        assert status.HTTP_404_NOT_FOUND in responses
        assert status.HTTP_409_CONFLICT in responses
        assert len(responses) == 2


class TestErrorsMergeExamples:
    """Tests for merging examples for the same status code."""
    
    def test_merge_error_dto_same_status(self, simple_error_dto):
        """Test merging examples from multiple ErrorDTO with same status code."""
        error1 = simple_error_dto(status_code=404, message="Error 1", detail="Error 1")
        error2 = simple_error_dto(status_code=404, message="Error 2", detail="Error 2")
        errors = Errors(error1, error2)
        responses = errors
        
        assert status.HTTP_404_NOT_FOUND in responses
        examples = responses[status.HTTP_404_NOT_FOUND]["content"]["application/json"]["examples"]
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
            unauthorized=True,  # Also adds 401
        )
        responses = errors
        
        assert status.HTTP_401_UNAUTHORIZED in responses
        # Dict should take precedence (or merge)
        examples = responses[status.HTTP_401_UNAUTHORIZED]["content"]["application/json"].get("examples", {})
        # Should have at least the dict example
        assert "InvalidToken" in examples or "default" in examples
    
    def test_merge_flag_and_error_dto_same_status(self, simple_error_dto):
        """Test merging flag and ErrorDTO for the same status code."""
        error_dto = simple_error_dto(status_code=401, message="Custom error", detail="Custom error")
        errors = Errors(
            error_dto,
            unauthorized=True,  # Also adds 401
        )
        responses = errors
        
        assert status.HTTP_401_UNAUTHORIZED in responses
        # ErrorDTO examples should be merged with flag example
        content = responses[status.HTTP_401_UNAUTHORIZED]["content"]["application/json"]
        assert "examples" in content or "example" in content


class TestErrorsMixed:
    """Tests for mixed usage (flags + dict + ErrorDTO)."""
    
    def test_mixed_flags_dict_error_dto(self, simple_error_dto):
        """Test mixed usage of flags, dict, and ErrorDTO."""
        error_dto = simple_error_dto(status_code=404, message="Not found", detail="Not found")
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
            unauthorized=True,
            forbidden=True,
        )
        responses = errors
        
        assert status.HTTP_401_UNAUTHORIZED in responses
        assert status.HTTP_403_FORBIDDEN in responses
        assert status.HTTP_404_NOT_FOUND in responses
        assert status.HTTP_409_CONFLICT in responses
        assert len(responses) == 4


class TestErrorsEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_errors(self):
        """Test empty Errors instance."""
        errors = Errors()
        responses = errors
        
        assert isinstance(responses, Mapping)
        assert len(responses) == 0
    
    def test_no_flags_no_errors(self):
        """Test Errors with no flags and no errors."""
        errors = Errors(
            unauthorized=False,
            forbidden=False,
            validation_error=False,
            internal_server_error=False,
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
    
    def test_errors_is_mapping(self):
        """Test that Errors implements Mapping protocol."""
        errors = Errors(unauthorized=True)
        
        assert isinstance(errors, Mapping)
        assert 401 in errors
        assert errors[401]["description"] == "Unauthorized"
        assert len(errors) == 1


class TestErrorsValidation:
    """Tests for ErrorDTO validation."""
    
    def test_valid_error_dto_passes(self, simple_error_dto):
        """Test that valid ErrorDTO passes validation."""
        error_dto = simple_error_dto(status_code=404, message="Not found", detail="Not found")
        errors = Errors(error_dto)
        responses = errors
        
        assert status.HTTP_404_NOT_FOUND in responses
    
    def test_missing_to_example_raises_typeerror(self):
        """Test that object without to_example raises TypeError."""
        class BadObject:
            status_code = 404
            message = "Test"
        
        with pytest.raises(TypeError) as exc_info:
            Errors(BadObject())
        
        assert "to_example" in str(exc_info.value)
        assert "BadObject" in str(exc_info.value)
    
    def test_missing_status_code_raises_typeerror(self):
        """Test that object without status_code raises TypeError."""
        class BadObject:
            message = "Test"
            def to_example(self):
                return {"test": {"value": {"detail": "test"}}}
        
        with pytest.raises(TypeError) as exc_info:
            Errors(BadObject())
        
        assert "status_code" in str(exc_info.value)
        assert "BadObject" in str(exc_info.value)
    
    def test_missing_message_raises_typeerror(self):
        """Test that object without message raises TypeError."""
        class BadObject:
            status_code = 404
            def to_example(self):
                return {"test": {"value": {"detail": "test"}}}
        
        with pytest.raises(TypeError) as exc_info:
            Errors(BadObject())
        
        assert "message" in str(exc_info.value)
        assert "BadObject" in str(exc_info.value)
    
    def test_non_callable_to_example_raises_typeerror(self):
        """Test that non-callable to_example raises TypeError."""
        class BadObject:
            status_code = 404
            message = "Test"
            to_example = "not a method"
        
        with pytest.raises(TypeError) as exc_info:
            Errors(BadObject())
        
        assert "to_example" in str(exc_info.value)
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
        assert "to_example" in error_msg
        assert "BadObject" in error_msg

