"""Gmail inbox search tool — mock implementation with real-API stub.

Set USE_REAL_GMAIL_API=1 in your .env (plus GOOGLE_CLIENT_ID,
GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN) to switch to the live API.
"""

from __future__ import annotations

import os

from .types import EmailMessage, EmailSearchRequest, EmailSearchResponse, ToolError


# ---------------------------------------------------------------------------
# Mock implementation (deterministic, no network calls)
# ---------------------------------------------------------------------------

_MOCK_MESSAGES = [
    EmailMessage(
        message_id="gmail_mock_001",
        subject="Your flight confirmation — AA 1234 ORD→JFK",
        from_address="noreply@aa.com",
        date_iso="2026-02-15T10:22:00Z",
        snippet="Your booking is confirmed. Flight AA 1234 departs Chicago O'Hare at 08:00 on Feb 22.",
    ),
    EmailMessage(
        message_id="gmail_mock_002",
        subject="Amtrak e-ticket — Chicago to Boston",
        from_address="noreply@amtrak.com",
        date_iso="2026-02-14T08:05:00Z",
        snippet="Thank you for booking with Amtrak. Train 449 departs Chicago Union Station at 19:45.",
    ),
    EmailMessage(
        message_id="gmail_mock_003",
        subject="Booking confirmed — Greyhound Bus CHI→NYC",
        from_address="noreply@greyhound.com",
        date_iso="2026-02-13T14:30:00Z",
        snippet="Your Greyhound ticket is ready. Departs Chicago at 22:00, arrives New York at 14:30.",
    ),
]


def _mock_gmail(payload: EmailSearchRequest) -> EmailSearchResponse | ToolError:
    if not payload.query.strip():
        return ToolError(
            type="validation", message="query is required", retryable=False
        )

    query_lower = payload.query.lower()
    # Simple keyword filter on mock data
    filtered = [
        m
        for m in _MOCK_MESSAGES
        if any(
            word in m.subject.lower() or word in m.snippet.lower()
            for word in query_lower.split()
        )
    ]
    if not filtered:
        filtered = _MOCK_MESSAGES  # fall back to all mocks if nothing matches

    return EmailSearchResponse(
        provider="gmail",
        messages=filtered[: payload.max_results],
    )


# ---------------------------------------------------------------------------
# Real-API stub (only active when USE_REAL_GMAIL_API=1)
# ---------------------------------------------------------------------------


def _real_gmail(
    payload: EmailSearchRequest,
) -> EmailSearchResponse | ToolError:  # pragma: no cover
    """Stub for real Gmail API via google-api-python-client."""
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
    service = build("gmail", "v1", credentials=creds)
    result = (
        service.users()
        .messages()
        .list(userId="me", q=payload.query, maxResults=payload.max_results)
        .execute()
    )
    message_ids = [m["id"] for m in result.get("messages", [])]
    messages: list[EmailMessage] = []
    for mid in message_ids:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=mid, format="metadata")
            .execute()
        )
        headers = {
            h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])
        }
        messages.append(
            EmailMessage(
                message_id=mid,
                subject=headers.get("Subject", "(no subject)"),
                from_address=headers.get("From", ""),
                date_iso=headers.get("Date", ""),
                snippet=msg.get("snippet", ""),
            )
        )
    return EmailSearchResponse(provider="gmail", messages=messages)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def gmail_tool(payload: EmailSearchRequest) -> EmailSearchResponse | ToolError:
    if os.environ.get("USE_REAL_GMAIL_API") == "1":
        return _real_gmail(payload)  # pragma: no cover
    return _mock_gmail(payload)
