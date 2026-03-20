from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class Parameter(BaseModel):
    name: str
    location: Literal["path", "query", "header", "cookie"]
    required: bool = False
    type_str: str = "str"
    description: str = ""
    default: Any = None


class RequestBody(BaseModel):
    content_type: str = "application/json"
    schema_dict: dict = Field(default_factory=dict)
    required: bool = True
    description: str = ""


class Endpoint(BaseModel):
    operation_id: str
    method: str
    path: str
    summary: str = ""
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    parameters: list[Parameter] = Field(default_factory=list)
    request_body: RequestBody | None = None


class AuthScheme(BaseModel):
    name: str
    type: str  # apiKey, http, oauth2
    location: str = "header"  # header, query, cookie
    header_name: str = "Authorization"
    scheme: str = ""  # bearer, basic


class APISpec(BaseModel):
    title: str
    description: str = ""
    version: str = "0.0.0"
    base_url: str = ""
    endpoints: list[Endpoint] = Field(default_factory=list)
    auth_schemes: list[AuthScheme] = Field(default_factory=list)
