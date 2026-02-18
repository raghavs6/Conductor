"""Auth token store — in-memory for MVP.

In production, replace with a persistent store (e.g. Redis or a DB)
and implement a real OAuth2 flow using the callback endpoints in main.py.

Environment variables (set in .env, never commit real values):
  GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN
  OUTLOOK_CLIENT_ID, OUTLOOK_CLIENT_SECRET, OUTLOOK_TENANT_ID, OUTLOOK_REFRESH_TOKEN
  AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TokenRecord:
    provider: str
    access_token: str
    refresh_token: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class InMemoryTokenStore:
    """Simple in-memory token store keyed by provider name."""

    def __init__(self) -> None:
        self._tokens: dict[str, TokenRecord] = {}
        self._load_from_env()

    def _load_from_env(self) -> None:
        """Pre-populate tokens from environment variables if present."""
        google_refresh = os.environ.get("GOOGLE_REFRESH_TOKEN")
        if google_refresh:
            self._tokens["google"] = TokenRecord(
                provider="google",
                access_token="",  # will be refreshed on first use
                refresh_token=google_refresh,
            )

        outlook_refresh = os.environ.get("OUTLOOK_REFRESH_TOKEN")
        if outlook_refresh:
            self._tokens["outlook"] = TokenRecord(
                provider="outlook",
                access_token="",
                refresh_token=outlook_refresh,
            )

    def save(self, record: TokenRecord) -> None:
        self._tokens[record.provider] = record

    def get(self, provider: str) -> TokenRecord | None:
        return self._tokens.get(provider)

    def delete(self, provider: str) -> None:
        self._tokens.pop(provider, None)


# Singleton used by the FastAPI app
TOKEN_STORE = InMemoryTokenStore()
