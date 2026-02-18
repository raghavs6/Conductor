"""Outlook Calendar tool — mock implementation with real-API stub.

Set USE_REAL_OUTLOOK_API=1 in your .env (plus OUTLOOK_CLIENT_ID,
OUTLOOK_CLIENT_SECRET, OUTLOOK_TENANT_ID, OUTLOOK_REFRESH_TOKEN) to
switch to the live Microsoft Graph API.
"""

from __future__ import annotations

import os

from .types import CalendarEvent, CalendarReadRequest, CalendarReadResponse, ToolError


# ---------------------------------------------------------------------------
# Mock implementation (deterministic, no network calls)
# ---------------------------------------------------------------------------

_MOCK_EVENTS = [
    CalendarEvent(
        event_id="outlook_mock_001",
        title="Weekly sync",
        start_iso="2026-02-20T10:00:00Z",
        end_iso="2026-02-20T10:30:00Z",
        location="Teams",
    ),
    CalendarEvent(
        event_id="outlook_mock_002",
        title="Flight to Boston",
        start_iso="2026-02-22T06:00:00Z",
        end_iso="2026-02-22T08:30:00Z",
        location="Boston, MA",
    ),
]


def _mock_calendar_outlook(
    payload: CalendarReadRequest,
) -> CalendarReadResponse | ToolError:
    if not payload.start_iso or not payload.end_iso:
        return ToolError(
            type="validation",
            message="start_iso and end_iso are required",
            retryable=False,
        )
    return CalendarReadResponse(provider="outlook", events=_MOCK_EVENTS)


# ---------------------------------------------------------------------------
# Real-API stub (only active when USE_REAL_OUTLOOK_API=1)
# ---------------------------------------------------------------------------


def _real_calendar_outlook(
    payload: CalendarReadRequest,
) -> CalendarReadResponse | ToolError:  # pragma: no cover
    """Stub for real Outlook via Microsoft Graph API (msal + requests)."""
    try:
        import msal  # type: ignore
        import requests  # type: ignore
    except ImportError:
        return ToolError(
            type="unknown",
            message="msal and requests not installed. Run: pip install msal requests",
            retryable=False,
        )

    app = msal.ConfidentialClientApplication(
        client_id=os.environ.get("OUTLOOK_CLIENT_ID", ""),
        client_credential=os.environ.get("OUTLOOK_CLIENT_SECRET", ""),
        authority=f"https://login.microsoftonline.com/{os.environ.get('OUTLOOK_TENANT_ID', 'common')}",
    )
    token_result = app.acquire_token_by_refresh_token(
        os.environ.get("OUTLOOK_REFRESH_TOKEN", ""),
        scopes=["Calendars.Read"],
    )
    if "access_token" not in token_result:
        return ToolError(
            type="auth", message="Failed to acquire Outlook token", retryable=True
        )

    headers = {"Authorization": f"Bearer {token_result['access_token']}"}
    url = (
        "https://graph.microsoft.com/v1.0/me/calendarView"
        f"?startDateTime={payload.start_iso}&endDateTime={payload.end_iso}"
        "&$orderby=start/dateTime&$top=50"
    )
    resp = requests.get(url, headers=headers, timeout=10)
    if not resp.ok:
        return ToolError(
            type="unknown",
            message=f"Graph API error: {resp.status_code}",
            retryable=True,
        )

    items = resp.json().get("value", [])
    events = [
        CalendarEvent(
            event_id=item["id"],
            title=item.get("subject", "(no title)"),
            start_iso=item["start"]["dateTime"],
            end_iso=item["end"]["dateTime"],
            location=item.get("location", {}).get("displayName"),
        )
        for item in items
    ]
    return CalendarReadResponse(provider="outlook", events=events)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def calendar_outlook_tool(
    payload: CalendarReadRequest,
) -> CalendarReadResponse | ToolError:
    if os.environ.get("USE_REAL_OUTLOOK_API") == "1":
        return _real_calendar_outlook(payload)  # pragma: no cover
    return _mock_calendar_outlook(payload)
