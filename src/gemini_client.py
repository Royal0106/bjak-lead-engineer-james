"""Gemini client helpers for fluent generation."""

from __future__ import annotations

import time
from typing import Any

from google import genai
from google.genai import types

from src.config import Settings


class GeminiClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = genai.Client(api_key=settings.gemini_api_key)

    def generate(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.45,
    ) -> tuple[str, dict[str, Any]]:
        """Returns (text, meta) where meta includes latency_ms and model."""
        last_err: Exception | None = None
        started = time.perf_counter()
        models_to_try = [
            self.settings.gemini_model,
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-flash-latest",
            "gemini-2.5-pro",
            "gemini-pro-latest",
        ]
        seen: set[str] = set()
        ordered: list[str] = []
        for m in models_to_try:
            if m and m not in seen:
                seen.add(m)
                ordered.append(m)

        for model in ordered:
            attempts = 1 if __import__("os").getenv("VERCEL") else 3
            for attempt in range(attempts):
                try:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=user,
                        config=types.GenerateContentConfig(
                            system_instruction=system,
                            temperature=temperature,
                            max_output_tokens=self.settings.max_output_tokens,
                        ),
                    )
                    text = (response.text or "").strip()
                    latency_ms = (time.perf_counter() - started) * 1000
                    return text, {
                        "latency_ms": latency_ms,
                        "model": model,
                        "attempts": attempt + 1,
                    }
                except Exception as exc:  # noqa: BLE001
                    last_err = exc
                    msg = str(exc)
                    if any(
                        code in msg
                        for code in (
                            "NOT_FOUND",
                            "FAILED_PRECONDITION",
                            "INVALID_ARGUMENT",
                            "PERMISSION_DENIED",
                            "RESOURCE_EXHAUSTED",
                            "429",
                        )
                    ):
                        break
                    if not __import__("os").getenv("VERCEL"):
                        time.sleep(1.0 * (attempt + 1))
        raise RuntimeError(f"Generation failed after retries: {last_err}") from last_err
