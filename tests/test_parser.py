from fastapi_to_skill.parser import parse_spec


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
