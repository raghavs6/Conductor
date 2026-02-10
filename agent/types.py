from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


class TraceEvent(BaseModel):
    type: str
    timestamp: str
    request_id: str
    payload: dict[str, Any] = Field(default_factory=dict)


class StateV1(BaseModel):
    version: Literal["v1"] = "v1"
    request_id: str
    user_message: str
    plan: list[dict[str, Any]] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    result: dict[str, Any] | None = None
    errors: list[str] = Field(default_factory=list)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
