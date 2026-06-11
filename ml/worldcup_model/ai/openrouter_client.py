import os
from typing import TypeVar

import httpx
from pydantic import ValidationError
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class OpenRouterStructuredClient:
    """Small adapter boundary for OpenRouter structured outputs.

    The concrete SDK call is intentionally left for the AI milestone so the math package
    stays importable without network credentials during the baseline milestone.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str = "https://openrouter.ai/api/v1",
        timeout_seconds: float | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.model = model or os.environ.get("OPENROUTER_MODEL", "openai/gpt-4.1-mini")
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds or float(os.environ.get("OPENROUTER_TIMEOUT_SECONDS", "25"))

    def complete_structured(
        self,
        messages: list[dict[str, str]],
        schema: type[T],
        *,
        use_web_search: bool = False,
    ) -> T:
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is required for AI enrichment jobs")

        body = self._request_body(messages, schema)
        return self._post_and_parse(body, schema, use_web_search=use_web_search)

    def parse_response(self, payload: str, schema: type[T]) -> T:
        return schema.model_validate_json(payload)

    def _request_body(self, messages: list[dict[str, str]], schema: type[T]) -> dict[str, object]:
        return {
            "model": self.model,
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "schema": schema.model_json_schema(),
                },
            },
        }

    def _fallback_request_body(self, messages: list[dict[str, str]], schema: type[T]) -> dict[str, object]:
        fallback_messages = [
            *messages,
            {
                "role": "user",
                "content": (
                    "Return only JSON matching this schema. Do not wrap it in Markdown. "
                    f"Schema: {schema.model_json_schema()}"
                ),
            },
        ]
        return {"model": self.model, "messages": fallback_messages}

    def _post_and_parse(self, body: dict[str, object], schema: type[T], *, use_web_search: bool) -> T:
        if use_web_search:
            body["plugins"] = [{"id": "web", "max_results": 5}]

        response = self._post(body)
        if response.status_code >= 400 and "response_format" in body:
            fallback_body = self._fallback_request_body(body["messages"], schema)
            if use_web_search:
                fallback_body["plugins"] = body.get("plugins", [])
            response = self._post(fallback_body)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"OpenRouter returned {response.status_code}: {response.text[:500]}"
            ) from exc

        payload = response.json()
        content = payload["choices"][0]["message"]["content"]
        try:
            return self.parse_response(content, schema)
        except ValidationError as exc:
            raise RuntimeError(f"OpenRouter returned non-matching JSON: {content[:500]}") from exc

    def _post(self, body: dict[str, object]) -> httpx.Response:
        try:
            return httpx.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": os.environ.get("OPENROUTER_SITE_URL", "https://kickweb.kncklab.com"),
                    "X-Title": os.environ.get("OPENROUTER_APP_TITLE", "WorldCupQuant"),
                },
                json=body,
                timeout=httpx.Timeout(self.timeout_seconds, connect=min(10.0, self.timeout_seconds)),
            )
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"OpenRouter request timed out after {self.timeout_seconds:.0f}s") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"OpenRouter request failed before response: {exc}") from exc
