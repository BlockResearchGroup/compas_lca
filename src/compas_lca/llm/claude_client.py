"""
Lightweight Claude client used by the one-shot classifier.

This avoids the pydantic-ai wrapper and keeps only the essentials:
- model name
- temperature/max_tokens
- direct API call
"""

import os
from typing import Optional

from anthropic import Anthropic


class ClaudeClient:
    """Tiny convenience wrapper around the Anthropic SDK."""

    def __init__(
        self,
        *,
        model: str = "claude-haiku-4-5",
        temperature: float = 0.0,
        max_tokens: int = 512,
        api_key: Optional[str] = None,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set.")
        self._client = Anthropic(api_key=self.api_key)

    def complete(self, prompt: str) -> str:
        """Send a single user-message prompt and return the concatenated text."""
        resp = self._client.messages.create(
            model="claude-haiku-4-5",
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        # Concatenate only text blocks for simplicity.
        parts = []
        for block in resp.content or []:
            if block.type == "text":
                parts.append(block.text)
        return "".join(parts)

