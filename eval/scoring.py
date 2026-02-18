from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ScoreResult:
    passed: bool
    reasons: list[str]
    tool_calls: list[dict[str, Any]]


def score_tool_calls(
    events: list[dict[str, Any]], expected_tools: list[str]
) -> ScoreResult:
    tool_calls: list[dict[str, Any]] = [
        event["payload"] for event in events if event.get("type") == "tool_called"
    ]

    called_tools = [call.get("tool_name") for call in tool_calls]
    called_tools_set = set(called_tools)
    reasons: list[str] = []

    for tool in expected_tools:
        if tool not in called_tools_set:
            reasons.append(f"missing expected tool call: {tool}")

    has_errors = any(call.get("error") for call in tool_calls)
    if has_errors:
        reasons.append("tool errors present in trace")

    return ScoreResult(passed=not reasons, reasons=reasons, tool_calls=tool_calls)
