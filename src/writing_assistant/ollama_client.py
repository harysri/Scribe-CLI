"""Ollama API client with streaming support."""

from __future__ import annotations

import json
import time
from typing import Any, AsyncIterator, Iterator

import httpx


class OllamaClient:
    """Simple synchronous Ollama client with streaming."""

    def __init__(self, host: str, model: str, temperature: float = 0.3, timeout: int = 60):
        self.host = host.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def generate(
        self,
        system: str,
        prompt: str,
        stream: bool = True,
        max_tokens: int = 2048,
    ) -> Iterator[str]:
        """Generate text with streaming. Yields token chunks."""
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "system": system,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": self.temperature,
                "num_predict": max_tokens,
            },
        }

        start_time = time.time()
        token_count = 0

        with self.client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                chunk = data.get("response", "")
                if chunk:
                    token_count += 1
                    yield chunk

                if data.get("done"):
                    break

        elapsed = time.time() - start_time
        safe_elapsed = max(elapsed, 0.001)
        yield f"\n\n[Stats: {token_count} tokens, {elapsed:.2f}s ({token_count/safe_elapsed:.1f} tok/s)]"

    def check_model(self) -> bool:
        """Check if the configured model is available."""
        try:
            resp = self.client.get(f"{self.host}/api/tags", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            models = [m["name"] for m in data.get("models", [])]
            return self.model in models or any(self.model in m for m in models)
        except Exception:
            return False

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> OllamaClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
