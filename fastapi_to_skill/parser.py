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


def _shorten_operation_id(op_id: str, method: str, path: str = "") -> str:
    """Shorten auto-generated FastAPI operationIds.

    Uses the URL path to detect where the function name ends and the path
    echo begins, so nested routes like ``/users/{user_id}/orders`` keep
    clean names (``create_order`` instead of ``create_order_users``).

    Examples:
      list_tasks_tasks_get       → list_tasks
      create_task_tasks_post     → create_task
      get_task_tasks_task_id_get → get_task
      delete_task_tasks_task_id_delete → delete_task
      create_order_users_user_id_orders_post → create_order
      get_stats_admin_stats_get → get_stats
      ban_user_admin_users_user_id_ban_delete → ban_user
    """
    # 1. Remove trailing HTTP method suffix
    method_lower = method.lower()
    if op_id.endswith(f"_{method_lower}"):
        op_id = op_id[: -len(f"_{method_lower}")]

    # 2. Build a set of path segment words to detect the path echo.
    #    e.g. /users/{user_id}/orders → {"users", "user", "id", "orders"}
    path_words: set[str] = set()
    if path:
        for segment in path.strip("/").split("/"):
            segment = re.sub(r"[{}]", "", segment)
            for word in segment.split("_"):
                if word:
                    path_words.add(word.lower())

    # 3. Split into parts and remove consecutive duplicates
    parts = op_id.split("_")
    deduped = []
    for part in parts:
        if not deduped or part != deduped[-1]:
            deduped.append(part)

    # 4. Find where the "semantic" prefix ends and the path echo begins.
    def _is_variant(word: str, seen: set[str]) -> bool:
        return (
            word in seen
            or word.rstrip("s") in seen  # tasks → task
            or f"{word}s" in seen        # task → tasks
        )

    # Build path segment names (full segments, not individual words).
    # e.g. /users/{user_id}/orders → ["users", "user_id", "orders"]
    path_segments: list[str] = []
    if path:
        for segment in path.strip("/").split("/"):
            cleaned = re.sub(r"[{}]", "", segment)
            if cleaned:
                path_segments.append(cleaned.lower())

    seen: set[str] = set()
    result = []
    for i, part in enumerate(deduped):
        # When we have path info: stop as soon as we find a sequence of
        # parts that matches the start of the path segments.
        # e.g. deduped = [create, order, users, user, id, orders]
        #      path_segments = [users, user_id, orders]
        # At "users" (index 2), remaining = [users, user, id, orders]
        # joined remainder starts with path content → stop here.
        if path_segments:
            remaining = "_".join(deduped[i:])
            first_seg = path_segments[0]
            if remaining.startswith(first_seg) and len(result) >= 2:
                break

        # Fallback: old heuristic for when no path is provided
        if not path_segments and _is_variant(part, seen):
            break
        seen.add(part)
        result.append(part)

    return "_".join(result) if result else "_".join(deduped)


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


def _deep_resolve_schema(schema: dict, spec: dict, *, _depth: int = 0) -> dict:
    """Recursively resolve $ref, anyOf, and allOf so the schema is self-contained.

    Resolves up to 5 levels deep to avoid infinite recursion with circular refs.
    """
    if _depth > 5:
        return schema

    # Resolve top-level $ref
    if "$ref" in schema:
        resolved = _resolve_ref(schema["$ref"], spec)
        # Preserve fields from the referencing schema (e.g. default)
        merged = {**resolved}
        for key, val in schema.items():
            if key != "$ref":
                merged[key] = val
        schema = merged
        return _deep_resolve_schema(schema, spec, _depth=_depth + 1)

    result = dict(schema)

    # Handle anyOf / oneOf — pick the first non-null type
    for combiner in ("anyOf", "oneOf"):
        if combiner in result:
            variants = result[combiner]
            non_null = [v for v in variants if v.get("type") != "null"]
            if non_null:
                resolved_variant = _deep_resolve_schema(non_null[0], spec, _depth=_depth + 1)
                # Merge the resolved variant into the result
                for key, val in resolved_variant.items():
                    if key not in result or key in ("type", "properties", "enum", "items", "required"):
                        result[key] = val
            del result[combiner]

    # Handle allOf — merge all schemas
    if "allOf" in result:
        merged_props: dict = {}
        merged_required: list = []
        for sub in result["allOf"]:
            resolved_sub = _deep_resolve_schema(sub, spec, _depth=_depth + 1)
            merged_props.update(resolved_sub.get("properties", {}))
            merged_required.extend(resolved_sub.get("required", []))
            for key, val in resolved_sub.items():
                if key not in ("properties", "required"):
                    result.setdefault(key, val)
        if merged_props:
            result["properties"] = merged_props
        if merged_required:
            result["required"] = merged_required
        del result["allOf"]

    # Recurse into properties
    if "properties" in result:
        resolved_props = {}
        for prop_name, prop_schema in result["properties"].items():
            resolved_props[prop_name] = _deep_resolve_schema(prop_schema, spec, _depth=_depth + 1)
        result["properties"] = resolved_props

    # Recurse into array items
    if result.get("type") == "array" and "items" in result:
        result["items"] = _deep_resolve_schema(result["items"], spec, _depth=_depth + 1)

    return result


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
            schema = _deep_resolve_schema(schema, spec)
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
            op_id = _shorten_operation_id(op_id, method, path)

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
