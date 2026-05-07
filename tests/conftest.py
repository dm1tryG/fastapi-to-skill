import pytest


@pytest.fixture
def complex_spec() -> dict:
    """Complex OpenAPI spec with nested models, enums, deep paths, multiple auth."""
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "E-Commerce API",
            "description": "Complex e-commerce API",
            "version": "2.0.0",
        },
        "servers": [{"url": "https://api.shop.com"}],
        "paths": {
            "/users": {
                "get": {
                    "operationId": "list_users_users_get",
                    "summary": "List Users",
                    "tags": ["users"],
                    "parameters": [
                        {
                            "name": "role",
                            "in": "query",
                            "required": False,
                            "schema": {
                                "enum": ["admin", "customer", "seller"],
                                "type": "string",
                            },
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {"type": "integer", "default": 50},
                        },
                    ],
                },
                "post": {
                    "operationId": "create_user_users_post",
                    "summary": "Create User",
                    "tags": ["users"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UserCreate"}
                            }
                        },
                    },
                },
            },
            "/users/{user_id}": {
                "put": {
                    "operationId": "update_user_users__user_id__put",
                    "summary": "Update User",
                    "tags": ["users"],
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        },
                        {
                            "name": "notify",
                            "in": "query",
                            "schema": {"type": "boolean", "default": False},
                        },
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UserCreate"}
                            }
                        },
                    },
                },
            },
            "/users/{user_id}/orders": {
                "get": {
                    "operationId": "list_user_orders_users__user_id__orders_get",
                    "summary": "List User Orders",
                    "tags": ["orders"],
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        },
                    ],
                },
                "post": {
                    "operationId": "create_order_users__user_id__orders_post",
                    "summary": "Create Order",
                    "tags": ["orders"],
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        },
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/OrderCreate"}
                            }
                        },
                    },
                },
            },
            "/users/{user_id}/orders/{order_id}": {
                "get": {
                    "operationId": "get_order_users__user_id__orders__order_id__get",
                    "summary": "Get Order",
                    "tags": ["orders"],
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        },
                        {
                            "name": "order_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        },
                    ],
                },
            },
            "/admin/stats": {
                "get": {
                    "operationId": "get_stats_admin_stats_get",
                    "summary": "Get Stats",
                    "tags": ["admin"],
                },
            },
        },
        "components": {
            "schemas": {
                "Address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string"},
                        "country": {"type": "string", "default": "US"},
                    },
                    "required": ["street", "city"],
                    "title": "Address",
                },
                "UserRole": {
                    "type": "string",
                    "enum": ["admin", "customer", "seller"],
                    "title": "UserRole",
                },
                "UserCreate": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "role": {
                            "$ref": "#/components/schemas/UserRole",
                            "default": "customer",
                        },
                        "address": {
                            "anyOf": [
                                {"$ref": "#/components/schemas/Address"},
                                {"type": "null"},
                            ]
                        },
                    },
                    "required": ["name", "email"],
                    "title": "UserCreate",
                },
                "OrderItem": {
                    "type": "object",
                    "properties": {
                        "product_id": {"type": "integer"},
                        "quantity": {"type": "integer", "default": 1},
                        "price": {"type": "number"},
                    },
                    "required": ["product_id", "price"],
                    "title": "OrderItem",
                },
                "OrderCreate": {
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/OrderItem"},
                        },
                        "shipping_address": {
                            "$ref": "#/components/schemas/Address"
                        },
                        "note": {"type": "string"},
                    },
                    "required": ["items", "shipping_address"],
                    "title": "OrderCreate",
                },
            },
            "securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer"},
                "apiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                },
            },
        },
    }


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
