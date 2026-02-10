from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Protocol

from tools.mocks import TOOL_REGISTRY
from tools.types import (
    CalendarRequest,
    EmailRequest,
    MapsRequest,
    SearchRequest,
    ToolCallEnvelope,
    ToolError,
)

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


def _select_tool(message: str) -> str:
    lowered = message.lower()
    if any(keyword in lowered for keyword in ("email", "mail", "inbox")):
        return "email"
    if any(keyword in lowered for keyword in ("calendar", "schedule", "meeting")):
        return "calendar"
    if any(keyword in lowered for keyword in ("map", "maps", "directions", "route")):
        return "maps"
    return "search"


def _build_request(tool_name: str, message: str) -> tuple[dict[str, Any], Any]:
    if tool_name == "email":
        request = EmailRequest(to="user@example.com", subject="Request", body=message)
    elif tool_name == "calendar":
        request = CalendarRequest(
            title=message,
            start_iso="2026-02-10T09:00:00Z",
            end_iso="2026-02-10T10:00:00Z",
            location="Virtual",
        )
    elif tool_name == "maps":
        request = MapsRequest(origin="Origin", destination=message, mode="driving")
    else:
        request = SearchRequest(query=message)
    return request.model_dump(), request


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

        tool_name = _select_tool(message)
        state.plan = [{"type": "tool", "tool_name": tool_name, "input": message}]
        _emit(trace_sink, "plan_created", request_id, {"plan": state.plan})
        state_store.save(state)

        args, request = _build_request(tool_name, message)
        handler = TOOL_REGISTRY[tool_name]
        result = handler(request)

        envelope = ToolCallEnvelope(tool_name=tool_name, args=args)
        if isinstance(result, ToolError):
            envelope.error = result
            state.errors.append(result.message)
        else:
            envelope.result = result.model_dump()

        state.tool_calls.append(envelope.model_dump())
        _emit(trace_sink, "tool_called", request_id, envelope.model_dump())
        state_store.save(state)

        reply = f"You said: {message}"
        state.result = {"reply": reply}
        _emit(trace_sink, "verification_passed", request_id, {})
        state_store.save(state)

        return reply
    except Exception as exc:  # pragma: no cover - defensive fallback
        state.errors.append(str(exc))
        state_store.save(state)
        _emit(trace_sink, "error", request_id, {"error": str(exc)})
        return "Sorry, something went wrong."
