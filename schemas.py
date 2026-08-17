"""Generated TubeAlfred tool schemas and request mapping adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import quote

from .generated_operations import OPERATIONS

PLUGIN_NAME = "tubealfred-youtube"
TOOLSET = "tubealfred_youtube"
VERSION = "0.1.4"
API_KEY_ENV = "TUBEALFRED_API_KEY"


@dataclass(frozen=True)
class RequestSpec:
    path: str
    method: str = "GET"
    query: dict[str, Any] | None = None
    body: dict[str, Any] | None = None


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]
    request: Callable[[dict[str, Any]], RequestSpec]


def _required_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required.")
    return value.strip()


def _optional_string(value: Any, name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string when provided.")
    return value.strip()


def _required_string_list(value: Any, name: str, maximum: int) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{name} must be a non-empty list.")
    if len(value) > maximum:
        raise ValueError(f"{name} must contain at most {maximum} items.")

    items = [_required_string(item, f"{name} item") for item in value]
    if len(set(items)) != len(items):
        raise ValueError(f"{name} items must be unique.")
    return items


def _parameter_value(parameter: dict[str, Any], params: dict[str, Any]) -> Any:
    name = parameter["name"]
    schema = parameter["schema"]
    required = parameter["required"]
    value = params.get(name)

    if schema.get("type") == "array":
        if value is None and not required:
            return None
        return _required_string_list(value, name, int(schema.get("maxItems", 50)))

    if schema.get("type") == "integer":
        if value is None:
            if required:
                raise ValueError(f"{name} is required.")
            return None
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"{name} must be an integer.")
        minimum = int(schema.get("minimum", 1))
        maximum = int(schema.get("maximum", 2**31 - 1))
        if value < minimum or value > maximum:
            raise ValueError(f"{name} must be between {minimum} and {maximum}.")
        return value

    if schema.get("type") == "boolean":
        if value is None:
            if required:
                raise ValueError(f"{name} is required.")
            return None
        if not isinstance(value, bool):
            raise ValueError(f"{name} must be a boolean.")
        return value

    allowed = schema.get("enum")
    if allowed is not None:
        text = _required_string(value, name) if required else _optional_string(value, name)
        if text is not None and text not in allowed:
            raise ValueError(f"{name} must be one of: {', '.join(allowed)}.")
        return text

    return _required_string(value, name) if required else _optional_string(value, name)


def _request(operation: dict[str, Any], params: dict[str, Any]) -> RequestSpec:
    path = operation["path"]
    query: dict[str, Any] = {}
    body: dict[str, Any] = {}

    for parameter in operation["request_parameters"]:
        value = _parameter_value(parameter, params)
        location = parameter["in"]
        name = parameter["name"]

        if location == "path":
            path = path.replace(f"{{{name}}}", quote(str(value), safe=""))
        elif location == "query" and value is not None:
            query[name] = value
        elif location == "body" and value is not None:
            body[name] = value

    return RequestSpec(
        path=path,
        method=operation["method"],
        query=query or None,
        body=body or None,
    )


def _tool(operation: dict[str, Any]) -> ToolDefinition:
    return ToolDefinition(
        name=operation["name"],
        description=operation["description"],
        parameters=operation["parameters"],
        request=lambda params: _request(operation, params),
    )


TOOLS: list[ToolDefinition] = [
    ToolDefinition(
        name="tubealfred_billing_usage",
        description="Fetch TubeAlfred credit balance and billing usage.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        request=lambda _params: RequestSpec(path="/v1/billing/usage"),
    ),
    *[_tool(operation) for operation in OPERATIONS],
]
