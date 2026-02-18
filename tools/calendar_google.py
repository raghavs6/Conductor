"""Google Calendar tool — mock implementation with real-API stub.

Set USE_REAL_GOOGLE_API=1 in your .env (plus GOOGLE_CLIENT_ID,
GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN) to switch to the live API.
"""

from __future__ import annotations

import hashlib
import os

from .types import CalendarEvent, CalendarReadRequest, CalendarReadResponse, ToolError


def _stable_id(value: str) -> str:
    return "gcal_" + hashlib.sha256(value.encode()).hexdigest()[:10]


# ---------------------------------------------------------------------------
# Mock implementation (deterministic, no network calls)
# ---------------------------------------------------------------------------

_MOCK_EVENTS = [
    CalendarEvent(
        event_id="gcal_mock_001",
        title="Team standup",
        start_iso="2026-02-20T09:00:00Z",
        end_iso="2026-02-20T09:30:00Z",
        location="Virtual",
    ),
    CalendarEvent(
        event_id="gcal_mock_002",
        title="Client presentation",
        start_iso="2026-02-21T14:00:00Z",
        end_iso="2026-02-21T15:00:00Z",
        location="Chicago, IL",
    ),
    CalendarEvent(
        event_id="gcal_mock_003",
        title="Travel to NYC",
        start_iso="2026-02-22T07:00:00Z",
        end_iso="2026-02-22T11:00:00Z",
        location="New York, NY",
    ),
]


def _mock_calendar_google(
    payload: CalendarReadRequest,
) -> CalendarReadResponse | ToolError:
    """Return a deterministic subset of mock events within the requested range."""
    if not payload.start_iso or not payload.end_iso:
        return ToolError(
            type="validation",
            message="start_iso and end_iso are required",
            retryable=False,
        )
    # For the mock, return all events (a real impl would filter by date range)
    return CalendarReadResponse(provider="google", events=_MOCK_EVENTS)


# ---------------------------------------------------------------------------
# Real-API stub (only active when USE_REAL_GOOGLE_API=1)
# ---------------------------------------------------------------------------


def _real_calendar_google(
    payload: CalendarReadRequest,
) -> CalendarReadResponse | ToolError:  # pragma: no cover
    """Stub for real Google Calendar API via google-api-python-client."""
    try:
        from google.oauth2.credentials import Credentials  # type: ignore
        from googleapiclient.discovery import build  # type: ignore
    except ImportError:
        return ToolError(
            type="unknown",
            message="google-api-python-client not installed. Run: pip install google-api-python-client google-auth",
            retryable=False,
        )

    creds = Credentials(
        token=None,
        refresh_token=os.environ.get("GOOGLE_REFRESH_TOKEN"),
        client_id=os.environ.get("GOOGLE_CLIENT_ID"),
        client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token",
    )
    service = build("calendar", "v3", credentials=creds)
    items = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=payload.start_iso,
            timeMax=payload.end_iso,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
        .get("items", [])
    )
    events = [
        CalendarEvent(
            event_id=item["id"],
            title=item.get("summary", "(no title)"),
            start_iso=item["start"].get("dateTime", item["start"].get("date", "")),
            end_iso=item["end"].get("dateTime", item["end"].get("date", "")),
            location=item.get("location"),
        )
        for item in items
    ]
    return CalendarReadResponse(provider="google", events=events)


# ---------------------------------------------------------------------------
# Public entry point — dispatches to mock or real
# ---------------------------------------------------------------------------


def calendar_google_tool(
    payload: CalendarReadRequest,
) -> CalendarReadResponse | ToolError:
    if os.environ.get("USE_REAL_GOOGLE_API") == "1":
        return _real_calendar_google(payload)  # pragma: no cover
    return _mock_calendar_google(payload)
