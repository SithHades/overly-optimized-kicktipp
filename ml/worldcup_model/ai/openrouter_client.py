import json
import os
from typing import TypeVar

import httpx
from pydantic import BaseModel
from pydantic import ValidationError

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
        self.timeout_seconds = timeout_seconds or float(os.environ.get("OPENROUTER_TIMEOUT_SECONDS", "180"))

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
        try:
            return schema.model_validate_json(payload)
        except (ValueError, ValidationError):
            extracted = _extract_json_object(payload)
            if extracted is None:
                raise
            return schema.model_validate(extracted)

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
            response = self._post(self._fallback_body_with_plugins(body, schema, use_web_search))

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
        except (ValueError, ValidationError, RuntimeError):
            healed = self._heal_response(content, schema)
            if healed is not None:
                return healed
            fallback_response = self._post(self._fallback_body_with_plugins(body, schema, use_web_search))
            try:
                fallback_response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise RuntimeError(
                    f"OpenRouter returned {fallback_response.status_code}: {fallback_response.text[:500]}"
                ) from exc
            fallback_content = fallback_response.json()["choices"][0]["message"]["content"]
            try:
                return self.parse_response(fallback_content, schema)
            except (ValueError, ValidationError, RuntimeError) as exc:
                raise RuntimeError(f"OpenRouter returned non-matching JSON: {fallback_content[:500]}") from exc

    def _heal_response(self, content: str, schema: type[T]) -> T | None:
        healing_body = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You repair model output into valid JSON. Return only JSON. "
                        "Do not add facts, do not use Markdown, and preserve the original content."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Repair this response so it matches the schema.\n\n"
                        f"Schema: {schema.model_json_schema()}\n\n"
                        f"Response:\n{content}"
                    ),
                },
            ],
        }
        try:
            response = self._post(healing_body)
            response.raise_for_status()
            healed_content = response.json()["choices"][0]["message"]["content"]
            return self.parse_response(healed_content, schema)
        except Exception:
            return None

    def _fallback_body_with_plugins(
        self,
        body: dict[str, object],
        schema: type[T],
        use_web_search: bool,
    ) -> dict[str, object]:
        messages = body["messages"]
        if not isinstance(messages, list):
            raise RuntimeError("OpenRouter request body is missing messages")
        fallback_body = self._fallback_request_body(messages, schema)
        if use_web_search:
            fallback_body["plugins"] = body.get("plugins", [])
        return fallback_body

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


def _extract_json_object(payload: str) -> dict[str, object] | None:
    decoder = json.JSONDecoder()
    cleaned = payload.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    for index, character in enumerate(cleaned):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(cleaned[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None
