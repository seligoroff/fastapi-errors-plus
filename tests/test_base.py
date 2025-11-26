"""Unit tests for BaseErrorDTO and StandardErrorDTO classes."""

import pytest
from fastapi import status

from fastapi_errors_plus import BaseErrorDTO, Errors, StandardErrorDTO


@pytest.mark.unit
class TestBaseErrorDTO:
    """Tests for BaseErrorDTO class."""
    
    def test_create_base_error_dto(self):
        """Test creating BaseErrorDTO with status_code and message."""
        error = BaseErrorDTO(
            status_code=404,
            message="Not found",
        )
        
        assert error.status_code == 404
        assert error.message == "Not found"
    
    def test_to_example_single_example(self):
        """Test to_example() returns correct format for single example."""
        error = BaseErrorDTO(
            status_code=404,
            message="Notification not found",
        )
        
        result = error.to_example()
        
        assert isinstance(result, dict)
        assert "Notification not found" in result
        assert result["Notification not found"] == {
            "value": {"detail": "Notification not found"},
        }
    
    def test_to_example_format(self):
        """Test to_example() returns correct OpenAPI format."""
        error = BaseErrorDTO(
            status_code=500,
            message="Internal server error",
        )
        
        result = error.to_example()
        
        # Check structure
        assert len(result) == 1
        key = list(result.keys())[0]
        assert key == "Internal server error"
        assert "value" in result[key]
        assert result[key]["value"] == {"detail": "Internal server error"}
    
    def test_works_with_errors_class(self):
        """Test BaseErrorDTO works with Errors() class."""
        error = BaseErrorDTO(
            status_code=404,
            message="Item not found",
        )
        
        errors = Errors(error)
        responses = errors
        
        assert status.HTTP_404_NOT_FOUND in responses
        assert responses[status.HTTP_404_NOT_FOUND]["description"] == "Item not found"
        assert "content" in responses[status.HTTP_404_NOT_FOUND]
        assert "application/json" in responses[status.HTTP_404_NOT_FOUND]["content"]
        examples = responses[status.HTTP_404_NOT_FOUND]["content"]["application/json"]["examples"]
        assert "Item not found" in examples
        assert examples["Item not found"]["value"] == {"detail": "Item not found"}


@pytest.mark.unit
class TestStandardErrorDTO:
    """Tests for StandardErrorDTO class."""
    
    def test_create_standard_error_dto_with_examples(self):
        """Test creating StandardErrorDTO with custom examples."""
        error = StandardErrorDTO(
            status_code=401,
            message="Unauthorized",
            examples={
                "InvalidToken": "Ошибка декодирования токена.",
                "SessionNotFound": "Сессия пользователя не была найдена.",
            },
        )
        
        assert error.status_code == 401
        assert error.message == "Unauthorized"
        assert error.examples is not None
        assert "InvalidToken" in error.examples
        assert "SessionNotFound" in error.examples
    
    def test_create_standard_error_dto_without_examples(self):
        """Test creating StandardErrorDTO without examples (defaults to message)."""
        error = StandardErrorDTO(
            status_code=403,
            message="Forbidden",
        )
        
        assert error.status_code == 403
        assert error.message == "Forbidden"
        assert error.examples is not None
        assert error.examples == {"Forbidden": "Forbidden"}
    
    def test_to_example_multiple_examples(self):
        """Test to_example() returns correct format for multiple examples."""
        error = StandardErrorDTO(
            status_code=401,
            message="Unauthorized",
            examples={
                "InvalidToken": "Ошибка декодирования токена.",
                "SessionNotFound": "Сессия пользователя не была найдена.",
            },
        )
        
        result = error.to_example()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "InvalidToken" in result
        assert "SessionNotFound" in result
        
        assert result["InvalidToken"] == {
            "value": {"detail": "Ошибка декодирования токена."},
        }
        assert result["SessionNotFound"] == {
            "value": {"detail": "Сессия пользователя не была найдена."},
        }
    
    def test_to_example_default_example(self):
        """Test to_example() with default example (when examples not provided)."""
        error = StandardErrorDTO(
            status_code=403,
            message="Forbidden",
        )
        
        result = error.to_example()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "Forbidden" in result
        assert result["Forbidden"] == {
            "value": {"detail": "Forbidden"},
        }
    
    def test_works_with_errors_class_single_example(self):
        """Test StandardErrorDTO works with Errors() class (single example)."""
        error = StandardErrorDTO(
            status_code=404,
            message="Not found",
        )
        
        errors = Errors(error)
        responses = errors
        
        assert status.HTTP_404_NOT_FOUND in responses
        examples = responses[status.HTTP_404_NOT_FOUND]["content"]["application/json"]["examples"]
        assert "Not found" in examples
    
    def test_works_with_errors_class_multiple_examples(self):
        """Test StandardErrorDTO works with Errors() class (multiple examples)."""
        error = StandardErrorDTO(
            status_code=401,
            message="Unauthorized",
            examples={
                "InvalidToken": "Ошибка декодирования токена.",
                "SessionNotFound": "Сессия пользователя не была найдена.",
            },
        )
        
        errors = Errors(error)
        responses = errors
        
        assert status.HTTP_401_UNAUTHORIZED in responses
        examples = responses[status.HTTP_401_UNAUTHORIZED]["content"]["application/json"]["examples"]
        assert "InvalidToken" in examples
        assert "SessionNotFound" in examples
        assert examples["InvalidToken"]["value"] == {"detail": "Ошибка декодирования токена."}
        assert examples["SessionNotFound"]["value"] == {"detail": "Сессия пользователя не была найдена."}
    
    def test_merges_with_standard_flags(self):
        """Test StandardErrorDTO merges correctly with standard flags."""
        error = StandardErrorDTO(
            status_code=401,
            message="Unauthorized",
            examples={
                "InvalidToken": "Ошибка декодирования токена.",
            },
        )
        
        errors = Errors(error, unauthorized=True)
        responses = errors
        
        assert status.HTTP_401_UNAUTHORIZED in responses
        examples = responses[status.HTTP_401_UNAUTHORIZED]["content"]["application/json"]["examples"]
        # Both examples should be present
        assert "StandardUnauthorized" in examples  # From flag
        assert "InvalidToken" in examples  # From StandardErrorDTO


@pytest.mark.unit
class TestBaseErrorDTOInheritance:
    """Tests for inheritance from BaseErrorDTO."""
    
    def test_can_inherit_from_base_error_dto(self):
        """Test that projects can inherit from BaseErrorDTO."""
        from dataclasses import dataclass
        
        @dataclass
        class CustomErrorDTO(BaseErrorDTO):
            code: str = ""
            
            def to_example(self):
                return {
                    f"{self.code}_{self.message}": {
                        "value": {
                            "detail": self.message,
                            "code": self.code,
                        },
                    },
                }
        
        error = CustomErrorDTO(
            status_code=404,
            message="Not found",
            code="ERR_404",
        )
        
        result = error.to_example()
        assert "ERR_404_Not found" in result
        assert result["ERR_404_Not found"]["value"]["code"] == "ERR_404"
    
    def test_inherited_class_works_with_errors(self):
        """Test that inherited class works with Errors() class."""
        from dataclasses import dataclass
        
        @dataclass
        class CustomErrorDTO(BaseErrorDTO):
            def to_example(self):
                return {
                    "Custom": {
                        "value": {"detail": self.message},
                    },
                }
        
        error = CustomErrorDTO(
            status_code=500,
            message="Custom error",
        )
        
        errors = Errors(error)
        responses = errors
        
        assert status.HTTP_500_INTERNAL_SERVER_ERROR in responses
        examples = responses[status.HTTP_500_INTERNAL_SERVER_ERROR]["content"]["application/json"]["examples"]
        assert "Custom" in examples


@pytest.mark.unit
class TestBaseErrorDTOCompatibility:
    """Tests for compatibility with structural typing (Protocol)."""
    
    def test_structural_typing_still_works(self):
        """Test that structural typing (Protocol) still works alongside BaseErrorDTO."""
        # Old-style class without inheritance
        class MyError:
            status_code = 404
            message = "Not found"
            
            def to_example(self):
                return {
                    "Not found": {
                        "value": {"detail": "Not found"},
                    },
                }
        
        # Should work through structural typing
        errors = Errors(MyError())
        responses = errors
        
        assert status.HTTP_404_NOT_FOUND in responses
    
    def test_mixed_usage_base_and_structural(self):
        """Test mixing BaseErrorDTO and structural typing in one Errors() call."""
        base_error = BaseErrorDTO(
            status_code=404,
            message="Not found",
        )
        
        # Structural typing class
        class MyError:
            status_code = 500
            message = "Server error"
            
            def to_example(self):
                return {
                    "Server error": {
                        "value": {"detail": "Server error"},
                    },
                }
        
        errors = Errors(base_error, MyError())
        responses = errors
        
        assert status.HTTP_404_NOT_FOUND in responses
        assert status.HTTP_500_INTERNAL_SERVER_ERROR in responses




