from __future__ import annotations

import re

from .models import APISpec, AuthScheme, Endpoint, Parameter, RequestBody

JSON_TYPE_MAP = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "array": "list",
    "object": "dict",
}

HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")


def _slugify(text: str) -> str:
    """Convert text to a snake_case slug suitable for Python identifiers."""
    text = re.sub(r"[{}]", "", text)
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text)
    text = text.strip("_").lower()
    return text


def _make_operation_id(method: str, path: str) -> str:
    """Generate an operation ID from method + path."""
    return _slugify(f"{method}_{path}")


def _resolve_ref(ref: str, spec: dict) -> dict:
    """Resolve a $ref pointer one level (e.g. '#/components/schemas/User')."""
    if not ref.startswith("#/"):
        return {}
    parts = ref.lstrip("#/").split("/")
    node = spec
    for part in parts:
        node = node.get(part, {})
    return node


def _resolve_schema(schema: dict, spec: dict) -> dict:
    """Resolve a schema, following $ref if present."""
    if "$ref" in schema:
        return _resolve_ref(schema["$ref"], spec)
    return schema


def _map_type(schema: dict, spec: dict) -> str:
    """Map a JSON Schema type to a Python type string."""
    schema = _resolve_schema(schema, spec)
    json_type = schema.get("type", "string")
    if json_type == "array":
        items = schema.get("items", {})
        inner = _map_type(items, spec)
        return f"list[{inner}]"
    return JSON_TYPE_MAP.get(json_type, "str")


def _parse_parameters(params: list[dict], spec: dict) -> list[Parameter]:
    """Parse a list of OpenAPI parameter objects."""
    result = []
    for p in params:
        if "$ref" in p:
            p = _resolve_ref(p["$ref"], spec)
        schema = p.get("schema", {})
        result.append(
            Parameter(
                name=p["name"],
                location=p.get("in", "query"),
                required=p.get("required", False),
                type_str=_map_type(schema, spec),
                description=p.get("description", ""),
                default=schema.get("default"),
            )
        )
    return result


def _parse_request_body(body: dict, spec: dict) -> RequestBody | None:
    """Parse an OpenAPI requestBody object."""
    if "$ref" in body:
        body = _resolve_ref(body["$ref"], spec)
    content = body.get("content", {})
    for content_type in ("application/json", "multipart/form-data", "application/x-www-form-urlencoded"):
        if content_type in content:
            schema = content[content_type].get("schema", {})
            schema = _resolve_schema(schema, spec)
            return RequestBody(
                content_type=content_type,
                schema_dict=schema,
                required=body.get("required", True),
                description=body.get("description", ""),
            )
    return None


def _parse_auth_schemes(spec: dict) -> list[AuthScheme]:
    """Parse securitySchemes from OpenAPI components."""
    schemes = spec.get("components", {}).get("securitySchemes", {})
    result = []
    for name, s in schemes.items():
        auth_type = s.get("type", "")
        if auth_type == "apiKey":
            result.append(
                AuthScheme(
                    name=name,
                    type="apiKey",
                    location=s.get("in", "header"),
                    header_name=s.get("name", "X-API-Key"),
                )
            )
        elif auth_type == "http":
            result.append(
                AuthScheme(
                    name=name,
                    type="http",
                    scheme=s.get("scheme", "bearer"),
                    header_name="Authorization",
                )
            )
        elif auth_type == "oauth2":
            result.append(
                AuthScheme(
                    name=name,
                    type="oauth2",
                    header_name="Authorization",
                    scheme="bearer",
                )
            )
    return result


def _get_base_url(spec: dict) -> str:
    """Extract base URL from the spec."""
    servers = spec.get("servers", [])
    if servers:
        return servers[0].get("url", "")
    # Swagger 2.0
    host = spec.get("host", "localhost")
    base_path = spec.get("basePath", "")
    scheme = (spec.get("schemes") or ["https"])[0]
    return f"{scheme}://{host}{base_path}"


def parse_spec(raw: dict) -> APISpec:
    """Parse a raw OpenAPI dict into an APISpec model."""
    endpoints: list[Endpoint] = []
    seen_ids: set[str] = set()

    for path, path_item in raw.get("paths", {}).items():
        # Path-level parameters apply to all methods
        path_params = path_item.get("parameters", [])

        for method in HTTP_METHODS:
            operation = path_item.get(method)
            if not operation:
                continue

            op_id = operation.get("operationId") or _make_operation_id(method, path)
            op_id = _slugify(op_id)

            # Handle collisions
            base_id = op_id
            counter = 2
            while op_id in seen_ids:
                op_id = f"{base_id}_{counter}"
                counter += 1
            seen_ids.add(op_id)

            # Merge path-level and operation-level parameters
            all_params = path_params + operation.get("parameters", [])
            parameters = _parse_parameters(all_params, raw)

            request_body = None
            if "requestBody" in operation:
                request_body = _parse_request_body(operation["requestBody"], raw)

            endpoints.append(
                Endpoint(
                    operation_id=op_id,
                    method=method.upper(),
                    path=path,
                    summary=operation.get("summary", ""),
                    description=operation.get("description", ""),
                    tags=operation.get("tags", []),
                    parameters=parameters,
                    request_body=request_body,
                )
            )

    return APISpec(
        title=raw.get("info", {}).get("title", "API"),
        description=raw.get("info", {}).get("description", ""),
        version=raw.get("info", {}).get("version", "0.0.0"),
        base_url=_get_base_url(raw),
        endpoints=endpoints,
        auth_schemes=_parse_auth_schemes(raw),
    )
