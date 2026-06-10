import os
from typing import TypeVar

import httpx
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
        timeout_seconds: float = 60.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.model = model or os.environ.get("OPENROUTER_MODEL", "openai/gpt-4.1-mini")
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def complete_structured(
        self,
        messages: list[dict[str, str]],
        schema: type[T],
        *,
        use_web_search: bool = False,
    ) -> T:
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is required for AI enrichment jobs")

        body: dict[str, object] = {
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
        if use_web_search:
            body["plugins"] = [{"id": "web", "max_results": 5}]

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=body,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload["choices"][0]["message"]["content"]
        return self.parse_response(content, schema)

    def parse_response(self, payload: str, schema: type[T]) -> T:
        return schema.model_validate_json(payload)
