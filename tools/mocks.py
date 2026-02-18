from __future__ import annotations

import hashlib
from typing import Any, Callable

from .calendar_google import calendar_google_tool
from .calendar_outlook import calendar_outlook_tool
from .gmail import gmail_tool
from .transport import transport_tool
from .types import (
    CalendarReadRequest,
    CalendarRequest,
    CalendarResponse,
    EmailRequest,
    EmailResponse,
    EmailSearchRequest,
    MapsRequest,
    MapsResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
    ToolError,
    TransportSearchRequest,
)


def _stable_id(value: str, prefix: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}_{digest}"


# ---------------------------------------------------------------------------
# Legacy mock tools (kept for backward compatibility)
# ---------------------------------------------------------------------------


def search_tool(payload: SearchRequest) -> SearchResponse | ToolError:
    query = payload.query.strip()
    if not query:
        return ToolError(
            type="validation", message="query is required", retryable=False
        )

    results = [
        SearchResult(
            title=f"Result for {query}",
            url=f"https://example.com/search?q={query.replace(' ', '+')}",
            snippet=f"Mock search result about {query}.",
        ),
    ]
    return SearchResponse(results=results)


def maps_tool(payload: MapsRequest) -> MapsResponse | ToolError:
    origin = payload.origin.strip()
    destination = payload.destination.strip()
    if not origin or not destination:
        return ToolError(
            type="validation", message="origin and destination are required"
        )

    distance_km = float(len(origin) + len(destination))
    duration_min = int(distance_km * 2)
    return MapsResponse(distance_km=distance_km, duration_min=duration_min)


def calendar_tool(payload: CalendarRequest) -> CalendarResponse | ToolError:
    if not payload.title or not payload.start_iso or not payload.end_iso:
        return ToolError(
            type="validation", message="title, start_iso, end_iso are required"
        )

    event_id = _stable_id(
        f"{payload.title}:{payload.start_iso}:{payload.end_iso}", "evt"
    )
    return CalendarResponse(event_id=event_id)


def email_tool(payload: EmailRequest) -> EmailResponse | ToolError:
    if not payload.to or not payload.subject or not payload.body:
        return ToolError(type="validation", message="to, subject, body are required")

    message_id = _stable_id(f"{payload.to}:{payload.subject}", "msg")
    return EmailResponse(message_id=message_id)


# ---------------------------------------------------------------------------
# Adapter wrappers so new tools fit the Any→Any registry signature
# ---------------------------------------------------------------------------


def _read_calendar_adapter(payload: Any) -> Any:
    if isinstance(payload, dict):
        payload = CalendarReadRequest(**payload)
    provider = getattr(payload, "provider", "google")
    if provider == "outlook":
        return calendar_outlook_tool(payload)
    return calendar_google_tool(payload)


def _search_gmail_adapter(payload: Any) -> Any:
    if isinstance(payload, dict):
        payload = EmailSearchRequest(**payload)
    return gmail_tool(payload)


def _search_transport_adapter(payload: Any) -> Any:
    if isinstance(payload, dict):
        payload = TransportSearchRequest(**payload)
    return transport_tool(payload)


def _search_adapter(payload: Any) -> Any:
    if isinstance(payload, dict):
        payload = SearchRequest(**payload)
    return search_tool(payload)


def _maps_adapter(payload: Any) -> Any:
    if isinstance(payload, dict):
        payload = MapsRequest(**payload)
    return maps_tool(payload)


def _calendar_adapter(payload: Any) -> Any:
    if isinstance(payload, dict):
        payload = CalendarRequest(**payload)
    return calendar_tool(payload)


def _email_adapter(payload: Any) -> Any:
    if isinstance(payload, dict):
        payload = EmailRequest(**payload)
    return email_tool(payload)


ToolHandler = Callable[[Any], Any]

TOOL_REGISTRY: dict[str, ToolHandler] = {
    # Legacy tools (with dict-accepting adapters)
    "search": _search_adapter,
    "maps": _maps_adapter,
    "calendar": _calendar_adapter,
    "email": _email_adapter,
    # New travel tools
    "read_calendar": _read_calendar_adapter,
    "search_gmail": _search_gmail_adapter,
    "search_transport": _search_transport_adapter,
}
