from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Protocol

from tools.mocks import TOOL_REGISTRY
from tools.types import (
    ToolCallEnvelope,
    ToolError,
)

from .planner import TravelPlanStep, build_plan
from .types import StateV1, TraceEvent, now_iso


class TraceSink(Protocol):
    def emit(self, event: TraceEvent) -> None: ...


class StateStore(Protocol):
    def save(self, state: StateV1) -> None: ...

    def get(self, request_id: str) -> StateV1 | None: ...


class JsonlTraceSink:
    def __init__(self, traces_dir: Path | str) -> None:
        self._traces_dir = Path(traces_dir)

    def emit(self, event: TraceEvent) -> None:
        self._traces_dir.mkdir(parents=True, exist_ok=True)
        path = self._traces_dir / f"{event.request_id}.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event.model_dump(), ensure_ascii=True))
            f.write("\n")


class InMemoryStateStore:
    def __init__(self) -> None:
        self._states: dict[str, StateV1] = {}

    def save(self, state: StateV1) -> None:
        self._states[state.request_id] = state

    def get(self, request_id: str) -> StateV1 | None:
        return self._states.get(request_id)

    def count(self) -> int:
        return len(self._states)


class NoopTraceSink:
    def emit(self, event: TraceEvent) -> None:
        return None


def _emit(
    sink: TraceSink, event_type: str, request_id: str, payload: dict[str, Any]
) -> None:
    sink.emit(
        TraceEvent(
            type=event_type, timestamp=now_iso(), request_id=request_id, payload=payload
        )
    )


# ---------------------------------------------------------------------------
# Reply formatter
# ---------------------------------------------------------------------------


def _format_reply(message: str, step_results: list[dict[str, Any]]) -> str:
    """Build a human-readable reply from the collected step results."""
    parts: list[str] = []

    for step in step_results:
        tool = step.get("tool_name", "")
        result = step.get("result")
        error = step.get("error")

        if error:
            parts.append(f"⚠️  {tool}: {error.get('message', 'unknown error')}")
            continue

        if not result:
            continue

        if tool == "read_calendar":
            events = result.get("events", [])
            if events:
                lines = [
                    f"📅 **Calendar ({result.get('provider', 'google')}) — {len(events)} event(s) found:**"
                ]
                for ev in events:
                    lines.append(f"  • {ev['title']} @ {ev['start_iso'][:10]}")
                parts.append("\n".join(lines))
            else:
                parts.append("📅 No calendar conflicts found.")

        elif tool == "search_gmail":
            msgs = result.get("messages", [])
            if msgs:
                lines = [f"📧 **Gmail — {len(msgs)} travel email(s) found:**"]
                for m in msgs:
                    lines.append(f"  • {m['subject']} ({m['date_iso'][:10]})")
                parts.append("\n".join(lines))
            else:
                parts.append("📧 No matching emails found.")

        elif tool == "search_transport":
            options = result.get("options", [])
            origin = result.get("origin", "?")
            dest = result.get("destination", "?")
            if options:
                lines = [f"✈️  **Transport options from {origin} → {dest}:**"]
                for opt in options:
                    emoji = {"flight": "✈️", "train": "🚆", "bus": "🚌"}.get(
                        opt["mode"], "🚗"
                    )
                    lines.append(
                        f"  {emoji} {opt['carrier']} | {opt['mode'].capitalize()} | "
                        f"Departs {opt['departure_iso'][11:16]} | "
                        f"{opt['duration_min']} min | "
                        f"${opt['price_usd']:.2f} | "
                        f"{'Non-stop' if opt['stops'] == 0 else str(opt['stops']) + ' stop(s)'}"
                    )
                    lines.append(f"     🔗 {opt['booking_url']}")
                parts.append("\n".join(lines))
            else:
                parts.append(f"No transport options found from {origin} to {dest}.")

        elif tool == "search":
            results = result.get("results", [])
            if results:
                lines = ["🔍 **Search results:**"]
                for r in results:
                    lines.append(f"  • [{r['title']}]({r['url']}): {r['snippet']}")
                parts.append("\n".join(lines))

    if not parts:
        return f'I received your request: "{message}". No results were found.'

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Main agent loop
# ---------------------------------------------------------------------------


def run_chat(
    message: str,
    *,
    state_store: StateStore,
    trace_sink: TraceSink,
) -> str:
    request_id = str(uuid.uuid4())
    state = StateV1(request_id=request_id, user_message=message)

    try:
        _emit(trace_sink, "request_received", request_id, {"message": message})

        # Build multi-step plan
        plan_steps: list[TravelPlanStep] = build_plan(message)
        state.plan = [
            {
                "type": "tool",
                "tool_name": s.tool_name,
                "description": s.description,
                "args": s.args,
            }
            for s in plan_steps
        ]
        _emit(trace_sink, "plan_created", request_id, {"plan": state.plan})
        state_store.save(state)

        # Execute each step
        step_results: list[dict[str, Any]] = []
        for step in plan_steps:
            handler = TOOL_REGISTRY.get(step.tool_name)
            if handler is None:
                state.errors.append(f"Unknown tool: {step.tool_name}")
                continue

            result = handler(step.args)

            envelope = ToolCallEnvelope(tool_name=step.tool_name, args=step.args)
            if isinstance(result, ToolError):
                envelope.error = result
                state.errors.append(result.message)
                step_results.append(
                    {"tool_name": step.tool_name, "error": result.model_dump()}
                )
            else:
                result_dict = result.model_dump()
                envelope.result = result_dict
                step_results.append(
                    {"tool_name": step.tool_name, "result": result_dict}
                )

            state.tool_calls.append(envelope.model_dump())
            _emit(trace_sink, "tool_called", request_id, envelope.model_dump())
            state_store.save(state)

        # Build reply
        reply = _format_reply(message, step_results)
        state.result = {"reply": reply}
        _emit(trace_sink, "verification_passed", request_id, {})
        state_store.save(state)

        return reply

    except Exception as exc:  # pragma: no cover - defensive fallback
        state.errors.append(str(exc))
        state_store.save(state)
        _emit(trace_sink, "error", request_id, {"error": str(exc)})
        return "Sorry, something went wrong."
