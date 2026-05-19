"""Tool handlers for TubeAlfred Hermes plugin."""

from __future__ import annotations

import json
import os
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from .schemas import API_KEY_ENV, RequestSpec, ToolDefinition, VERSION

PRODUCT_NAME = "TubeAlfred Hermes plugin"
API_BASE_URL = "https://api.tubealfred.com"
TIMEOUT_SECONDS = 30
RETRIES = 1


def handle_tool(tool: ToolDefinition) -> Callable[..., str]:
    def handler(params: dict[str, Any], **kwargs: Any) -> str:
        del kwargs
        try:
            data = request_tubealfred(tool.request(params or {}))
            return json.dumps({"success": True, "data": data}, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False)

    return handler


def has_api_key() -> bool:
    return bool(get_env(API_KEY_ENV))


def get_env(name: str) -> str:
    try:
        from hermes_cli.config import get_env_value

        value = get_env_value(name)
    except Exception:
        value = os.environ.get(name)

    return value.strip() if isinstance(value, str) else ""


def request_tubealfred(spec: RequestSpec) -> Any:
    api_key = get_env(API_KEY_ENV)
    if not api_key:
        raise RuntimeError(f"Missing {API_KEY_ENV}. Set it in Hermes or your environment.")
    if not api_key.startswith(("ta_live_", "ta_test_")):
        raise RuntimeError(f"{API_KEY_ENV} must look like ta_live_... or ta_test_....")

    url = build_url(spec.path, spec.query)
    payload = None if spec.body is None else json.dumps(spec.body).encode("utf-8")
    request = Request(
        url,
        data=payload,
        method=spec.method,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"tubealfred-hermes/{VERSION} ({PRODUCT_NAME})",
        },
    )

    last_error: Exception | None = None
    for attempt in range(RETRIES + 1):
        try:
            with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            if attempt < RETRIES and exc.code in {408, 429, 500, 502, 503, 504}:
                time.sleep(0.25 * (attempt + 1))
                continue
            raise RuntimeError(f"TubeAlfred API request failed with HTTP {exc.code}: {raw}") from exc
        except URLError as exc:
            last_error = exc
            if attempt < RETRIES:
                time.sleep(0.25 * (attempt + 1))
                continue
            raise RuntimeError(f"TubeAlfred API request failed: {exc.reason}") from exc

    raise RuntimeError(f"TubeAlfred API request failed: {last_error}")


def build_url(path: str, query: dict[str, Any] | None = None) -> str:
    url = urljoin(f"{API_BASE_URL}/", path.lstrip("/"))
    clean_query = {
        key: value
        for key, value in (query or {}).items()
        if value is not None
    }
    if clean_query:
        url = f"{url}?{urlencode(clean_query)}"
    return url
