"""Integration tests with FastAPI."""

from fastapi import status
from fastapi.testclient import TestClient

from tests.test_app import app


class TestOpenAPIGeneration:
    """Tests for OpenAPI specification generation."""
    
    def test_openapi_schema_exists(self):
        """Test that OpenAPI schema is generated."""
        client = TestClient(app)
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
        assert "info" in schema
    
    def test_all_endpoints_in_openapi(self):
        """Test that all 7 test endpoints are in OpenAPI schema."""
        client = TestClient(app)
        response = client.get("/openapi.json")
        schema = response.json()
        
        paths = schema["paths"]
        assert "/api/v1/standard-flags" in paths
        assert "/api/v1/dict-errors/{item_id}" in paths
        assert "/api/v1/error-dto/{resource_id}" in paths
        assert "/api/v1/mixed/{item_id}" in paths
        assert "/api/v1/merge-examples/{item_id}" in paths
        assert "/api/v1/empty-errors" in paths
        assert "/api/v1/merge-flag-dict/{item_id}" in paths


class TestStandardFlagsEndpoint:
    """Tests for standard flags endpoint."""
    
    def test_responses_in_openapi(self):
        """Test that standard flags responses are in OpenAPI."""
        client = TestClient(app)
        response = client.get("/openapi.json")
        schema = response.json()
        
        endpoint = schema["paths"]["/api/v1/standard-flags"]["get"]
        responses = endpoint["responses"]
        
        assert "401" in responses
        assert "403" in responses
        assert "422" in responses
        assert "500" in responses
    
    def test_401_response_structure(self):
        """Test 401 response structure in OpenAPI."""
        client = TestClient(app)
        response = client.get("/openapi.json")
        schema = response.json()
        
        endpoint = schema["paths"]["/api/v1/standard-flags"]["get"]
        error_401 = endpoint["responses"]["401"]
        
        assert error_401["description"] == "Unauthorized"
        assert "content" in error_401
        assert "application/json" in error_401["content"]
        assert "example" in error_401["content"]["application/json"]


class TestDictErrorsEndpoint:
    """Tests for dict errors endpoint."""
    
    def test_responses_in_openapi(self):
        """Test that dict errors responses are in OpenAPI."""
        client = TestClient(app)
        response = client.get("/openapi.json")
        schema = response.json()
        
        endpoint = schema["paths"]["/api/v1/dict-errors/{item_id}"]["delete"]
        responses = endpoint["responses"]
        
        assert "404" in responses
        assert "409" in responses
    
    def test_404_response_structure(self):
        """Test 404 response structure from dict."""
        client = TestClient(app)
        response = client.get("/openapi.json")
        schema = response.json()
        
        endpoint = schema["paths"]["/api/v1/dict-errors/{item_id}"]["delete"]
        error_404 = endpoint["responses"]["404"]
        
        assert error_404["description"] == "Item not found"
        assert "content" in error_404
        assert "application/json" in error_404["content"]


class TestErrorDTOEndpoint:
    """Tests for ErrorDTO endpoint."""
    
    def test_responses_in_openapi(self):
        """Test that ErrorDTO responses are in OpenAPI."""
        client = TestClient(app)
        response = client.get("/openapi.json")
        schema = response.json()
        
        endpoint = schema["paths"]["/api/v1/error-dto/{resource_id}"]["get"]
        responses = endpoint["responses"]
        
        assert "404" in responses
    
    def test_404_response_structure_from_error_dto(self):
        """Test 404 response structure from ErrorDTO."""
        client = TestClient(app)
        response = client.get("/openapi.json")
        schema = response.json()
        
        endpoint = schema["paths"]["/api/v1/error-dto/{resource_id}"]["get"]
        error_404 = endpoint["responses"]["404"]
        
        assert error_404["description"] == "Resource not found"
        assert "content" in error_404
        assert "application/json" in error_404["content"]
        assert "examples" in error_404["content"]["application/json"]


class TestMixedEndpoint:
    """Tests for mixed endpoint (flags + dict + ErrorDTO)."""
    
    def test_all_responses_in_openapi(self):
        """Test that all mixed responses are in OpenAPI."""
        client = TestClient(app)
        response = client.get("/openapi.json")
        schema = response.json()
        
        endpoint = schema["paths"]["/api/v1/mixed/{item_id}"]["post"]
        responses = endpoint["responses"]
        
        assert "401" in responses  # From flag
        assert "403" in responses  # From flag
        assert "404" in responses  # From ErrorDTO
        assert "409" in responses  # From dict
    
    def test_mixed_responses_structure(self):
        """Test structure of mixed responses."""
        client = TestClient(app)
        response = client.get("/openapi.json")
        schema = response.json()
        
        endpoint = schema["paths"]["/api/v1/mixed/{item_id}"]["post"]
        responses = endpoint["responses"]
        
        # Check 401 from flag
        assert responses["401"]["description"] == "Unauthorized"
        
        # Check 404 from ErrorDTO
        assert responses["404"]["description"] == "Not found"
        assert "examples" in responses["404"]["content"]["application/json"]
        
        # Check 409 from dict
        assert responses["409"]["description"] == "Conflict"


class TestMergeExamplesEndpoint:
    """Tests for merge examples endpoint."""
    
    def test_merged_examples_in_openapi(self):
        """Test that merged examples are in OpenAPI."""
        client = TestClient(app)
        response = client.get("/openapi.json")
        schema = response.json()
        
        endpoint = schema["paths"]["/api/v1/merge-examples/{item_id}"]["put"]
        responses = endpoint["responses"]
        
        assert "404" in responses
        examples = responses["404"]["content"]["application/json"]["examples"]
        
        # Should have multiple examples merged
        assert len(examples) >= 2
        assert "Error 1" in examples
        assert "Error 2" in examples


class TestEmptyErrorsEndpoint:
    """Tests for empty errors endpoint."""
    
    def test_no_responses_in_openapi(self):
        """Test that empty Errors produces no error responses."""
        client = TestClient(app)
        response = client.get("/openapi.json")
        schema = response.json()
        
        endpoint = schema["paths"]["/api/v1/empty-errors"]["get"]
        responses = endpoint["responses"]
        
        # Should only have 200 (success response)
        assert "200" in responses
        # Should not have error responses (401, 403, etc.)
        error_codes = [code for code in responses.keys() if code.startswith("4") or code.startswith("5")]
        assert len(error_codes) == 0


class TestMergeFlagDictEndpoint:
    """Tests for merge flag and dict endpoint."""
    
    def test_merged_flag_and_dict_in_openapi(self):
        """Test that merged flag and dict are in OpenAPI."""
        client = TestClient(app)
        response = client.get("/openapi.json")
        schema = response.json()
        
        endpoint = schema["paths"]["/api/v1/merge-flag-dict/{item_id}"]["delete"]
        responses = endpoint["responses"]
        
        assert "401" in responses
        examples = responses["401"]["content"]["application/json"]["examples"]
        
        # Should have examples from dict
        assert "InvalidToken" in examples
        assert "SessionNotFound" in examples


class TestRealEndpoints:
    """Tests for actual endpoint responses."""
    
    def test_standard_flags_endpoint_works(self):
        """Test that standard flags endpoint returns 200."""
        client = TestClient(app)
        response = client.get("/api/v1/standard-flags")
        
        assert response.status_code == 200
        assert response.json() == {"message": "Standard flags example"}
    
    def test_empty_errors_endpoint_works(self):
        """Test that empty errors endpoint returns 200."""
        client = TestClient(app)
        response = client.get("/api/v1/empty-errors")
        
        assert response.status_code == 200
        assert response.json() == {"message": "No errors"}
    
    def test_dict_errors_endpoint_works(self):
        """Test that dict errors endpoint returns 200."""
        client = TestClient(app)
        response = client.delete("/api/v1/dict-errors/1")
        
        assert response.status_code == 200
        assert response.json() == {"message": "Item 1 deleted"}

