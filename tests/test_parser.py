from fastapi_to_skill.parser import parse_spec, _shorten_operation_id


def test_parse_endpoints(petstore_spec):
    api = parse_spec(petstore_spec)
    assert api.title == "Petstore"
    assert api.version == "1.0.0"
    assert api.base_url == "https://petstore.example.com/v1"
    assert len(api.endpoints) == 4


def test_parse_operation_ids(petstore_spec):
    api = parse_spec(petstore_spec)
    ids = {ep.operation_id for ep in api.endpoints}
    assert ids == {"list_pets", "create_pet", "get_pet", "delete_pet"}


def test_parse_parameters(petstore_spec):
    api = parse_spec(petstore_spec)
    list_pets = next(ep for ep in api.endpoints if ep.operation_id == "list_pets")
    assert len(list_pets.parameters) == 1
    assert list_pets.parameters[0].name == "limit"
    assert list_pets.parameters[0].type_str == "int"
    assert list_pets.parameters[0].default == 20


def test_parse_path_params(petstore_spec):
    api = parse_spec(petstore_spec)
    get_pet = next(ep for ep in api.endpoints if ep.operation_id == "get_pet")
    path_params = [p for p in get_pet.parameters if p.location == "path"]
    assert len(path_params) == 1
    assert path_params[0].name == "petId"
    assert path_params[0].required is True


def test_parse_request_body(petstore_spec):
    api = parse_spec(petstore_spec)
    create_pet = next(ep for ep in api.endpoints if ep.operation_id == "create_pet")
    assert create_pet.request_body is not None
    assert create_pet.request_body.content_type == "application/json"
    assert "name" in create_pet.request_body.schema_dict.get("properties", {})


def test_parse_auth_schemes(petstore_spec):
    api = parse_spec(petstore_spec)
    assert len(api.auth_schemes) == 1
    assert api.auth_schemes[0].type == "http"
    assert api.auth_schemes[0].scheme == "bearer"


def test_parse_no_operation_id():
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/items": {
                "get": {"summary": "List items"},
            }
        },
    }
    api = parse_spec(spec)
    assert len(api.endpoints) == 1
    assert api.endpoints[0].operation_id == "get_items"


# --- Complex spec tests ---


def test_complex_operation_ids(complex_spec):
    api = parse_spec(complex_spec)
    ids = {ep.operation_id for ep in api.endpoints}
    assert "list_users" in ids
    assert "create_user" in ids
    assert "update_user" in ids
    assert "list_user_orders" in ids
    assert "create_order" in ids
    assert "get_order" in ids
    assert "get_stats" in ids


def test_complex_nested_path_naming():
    """Deep nested paths should produce clean short names."""
    cases = [
        ("create_order_users_user_id_orders_post", "post", "/users/{user_id}/orders", "create_order"),
        ("get_order_users_user_id_orders_order_id_get", "get", "/users/{user_id}/orders/{order_id}", "get_order"),
        ("get_stats_admin_stats_get", "get", "/admin/stats", "get_stats"),
        ("ban_user_admin_users_user_id_ban_delete", "delete", "/admin/users/{user_id}/ban", "ban_user"),
    ]
    for op_id, method, path, expected in cases:
        result = _shorten_operation_id(op_id, method, path)
        assert result == expected, f"{op_id} → {result}, expected {expected}"


def test_complex_multiple_auth_schemes(complex_spec):
    api = parse_spec(complex_spec)
    assert len(api.auth_schemes) == 2
    types = {s.type for s in api.auth_schemes}
    assert "http" in types
    assert "apiKey" in types


def test_complex_ref_resolution_in_body(complex_spec):
    """$ref in request body should be fully resolved."""
    api = parse_spec(complex_spec)
    create_user = next(ep for ep in api.endpoints if ep.operation_id == "create_user")
    schema = create_user.request_body.schema_dict
    props = schema["properties"]
    # name and email should be present
    assert "name" in props
    assert "email" in props
    # role should have enum values (resolved from $ref)
    assert "enum" in props["role"]
    assert props["role"]["enum"] == ["admin", "customer", "seller"]
    # address should be resolved from anyOf + $ref
    assert props["address"].get("type") == "object"
    assert "street" in props["address"].get("properties", {})


def test_complex_nested_array_resolution(complex_spec):
    """Array items with $ref should be resolved."""
    api = parse_spec(complex_spec)
    create_order = next(ep for ep in api.endpoints if ep.operation_id == "create_order")
    schema = create_order.request_body.schema_dict
    items_field = schema["properties"]["items"]
    assert items_field["type"] == "array"
    # items should have resolved OrderItem schema
    item_schema = items_field["items"]
    assert "product_id" in item_schema.get("properties", {})
    assert "price" in item_schema.get("properties", {})


def test_complex_query_plus_body_endpoint(complex_spec):
    """Endpoint with both query params and body should have both."""
    api = parse_spec(complex_spec)
    update_user = next(ep for ep in api.endpoints if ep.operation_id == "update_user")
    query_params = [p for p in update_user.parameters if p.location == "query"]
    path_params = [p for p in update_user.parameters if p.location == "path"]
    assert len(query_params) == 1
    assert query_params[0].name == "notify"
    assert len(path_params) == 1
    assert path_params[0].name == "user_id"
    assert update_user.request_body is not None


def test_complex_collision_detection():
    """Duplicate operation IDs should get _2 suffix."""
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/a": {"get": {"operationId": "do_thing", "summary": "A"}},
            "/b": {"get": {"operationId": "do_thing", "summary": "B"}},
        },
    }
    api = parse_spec(spec)
    ids = [ep.operation_id for ep in api.endpoints]
    assert "do_thing" in ids
    assert "do_thing_2" in ids
