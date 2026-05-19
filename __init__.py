"""TubeAlfred YouTube tools for Hermes."""

from __future__ import annotations

from typing import Any

from .schemas import API_KEY_ENV, TOOLSET, TOOLS
from .tools import handle_tool, has_api_key


def register(ctx: Any) -> None:
    for tool in TOOLS:
        ctx.register_tool(
            name=tool.name,
            toolset=TOOLSET,
            schema={
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            },
            handler=handle_tool(tool),
            check_fn=has_api_key,
            requires_env=[API_KEY_ENV],
            description=tool.description,
        )
