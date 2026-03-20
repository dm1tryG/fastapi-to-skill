import pytest


@pytest.fixture
def petstore_spec() -> dict:
    """Minimal Petstore-like OpenAPI 3 spec for testing."""
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Petstore",
            "description": "A sample Petstore API",
            "version": "1.0.0",
        },
        "servers": [{"url": "https://petstore.example.com/v1"}],
        "paths": {
            "/pets": {
                "get": {
                    "operationId": "list_pets",
                    "summary": "List all pets",
                    "tags": ["pets"],
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "default": 20},
                            "description": "Max number of pets to return",
                        }
                    ],
                },
                "post": {
                    "operationId": "create_pet",
                    "summary": "Create a pet",
                    "tags": ["pets"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "tag": {"type": "string"},
                                    },
                                    "required": ["name"],
                                }
                            }
                        },
                    },
                },
            },
            "/pets/{petId}": {
                "get": {
                    "operationId": "get_pet",
                    "summary": "Get a pet by ID",
                    "tags": ["pets"],
                    "parameters": [
                        {
                            "name": "petId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "The ID of the pet",
                        }
                    ],
                },
                "delete": {
                    "operationId": "delete_pet",
                    "summary": "Delete a pet",
                    "tags": ["pets"],
                    "parameters": [
                        {
                            "name": "petId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                },
            },
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                }
            }
        },
    }
