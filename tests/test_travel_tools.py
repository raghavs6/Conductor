"""Tests for the new travel tools (calendar, gmail, transport)."""

from __future__ import annotations

from tools.calendar_google import calendar_google_tool
from tools.calendar_outlook import calendar_outlook_tool
from tools.gmail import gmail_tool
from tools.transport import transport_tool
from tools.types import (
    CalendarReadRequest,
    EmailSearchRequest,
    TransportSearchRequest,
    ToolError,
)


# ---------------------------------------------------------------------------
# Google Calendar
# ---------------------------------------------------------------------------


class TestCalendarGoogle:
    def test_returns_events(self) -> None:
        req = CalendarReadRequest(
            provider="google",
            start_iso="2026-02-20T00:00:00Z",
            end_iso="2026-02-22T23:59:59Z",
        )
        result = calendar_google_tool(req)
        assert not isinstance(result, ToolError)
        assert len(result.events) > 0
        assert result.provider == "google"

    def test_deterministic(self) -> None:
        req = CalendarReadRequest(
            provider="google",
            start_iso="2026-02-20T00:00:00Z",
            end_iso="2026-02-22T23:59:59Z",
        )
        assert calendar_google_tool(req) == calendar_google_tool(req)

    def test_validation_error_on_missing_dates(self) -> None:
        req = CalendarReadRequest(provider="google", start_iso="", end_iso="")
        result = calendar_google_tool(req)
        assert isinstance(result, ToolError)
        assert result.type == "validation"


# ---------------------------------------------------------------------------
# Outlook Calendar
# ---------------------------------------------------------------------------


class TestCalendarOutlook:
    def test_returns_events(self) -> None:
        req = CalendarReadRequest(
            provider="outlook",
            start_iso="2026-02-20T00:00:00Z",
            end_iso="2026-02-22T23:59:59Z",
        )
        result = calendar_outlook_tool(req)
        assert not isinstance(result, ToolError)
        assert len(result.events) > 0
        assert result.provider == "outlook"

    def test_deterministic(self) -> None:
        req = CalendarReadRequest(
            provider="outlook",
            start_iso="2026-02-20T00:00:00Z",
            end_iso="2026-02-22T23:59:59Z",
        )
        assert calendar_outlook_tool(req) == calendar_outlook_tool(req)


# ---------------------------------------------------------------------------
# Gmail
# ---------------------------------------------------------------------------


class TestGmail:
    def test_returns_messages(self) -> None:
        req = EmailSearchRequest(provider="gmail", query="flight confirmation")
        result = gmail_tool(req)
        assert not isinstance(result, ToolError)
        assert len(result.messages) > 0
        assert result.provider == "gmail"

    def test_deterministic(self) -> None:
        req = EmailSearchRequest(provider="gmail", query="train")
        assert gmail_tool(req) == gmail_tool(req)

    def test_validation_error_on_empty_query(self) -> None:
        req = EmailSearchRequest(provider="gmail", query="")
        result = gmail_tool(req)
        assert isinstance(result, ToolError)
        assert result.type == "validation"

    def test_max_results_respected(self) -> None:
        req = EmailSearchRequest(provider="gmail", query="flight", max_results=1)
        result = gmail_tool(req)
        assert not isinstance(result, ToolError)
        assert len(result.messages) <= 1


# ---------------------------------------------------------------------------
# Transport
# ---------------------------------------------------------------------------


class TestTransport:
    def test_returns_options_any_mode(self) -> None:
        req = TransportSearchRequest(
            origin="Chicago", destination="New York", departure_date="2026-02-22"
        )
        result = transport_tool(req)
        assert not isinstance(result, ToolError)
        assert len(result.options) > 0

    def test_sorted_by_price(self) -> None:
        req = TransportSearchRequest(
            origin="Chicago", destination="New York", departure_date="2026-02-22"
        )
        result = transport_tool(req)
        assert not isinstance(result, ToolError)
        prices = [o.price_usd for o in result.options]
        assert prices == sorted(prices)

    def test_flight_only_mode(self) -> None:
        req = TransportSearchRequest(
            origin="Chicago",
            destination="New York",
            departure_date="2026-02-22",
            mode="flight",
        )
        result = transport_tool(req)
        assert not isinstance(result, ToolError)
        assert all(o.mode == "flight" for o in result.options)

    def test_train_only_mode(self) -> None:
        req = TransportSearchRequest(
            origin="Chicago",
            destination="Boston",
            departure_date="2026-02-22",
            mode="train",
        )
        result = transport_tool(req)
        assert not isinstance(result, ToolError)
        assert all(o.mode == "train" for o in result.options)

    def test_deterministic(self) -> None:
        req = TransportSearchRequest(
            origin="Chicago", destination="New York", departure_date="2026-02-22"
        )
        assert transport_tool(req) == transport_tool(req)

    def test_validation_error_on_missing_origin(self) -> None:
        req = TransportSearchRequest(
            origin="", destination="New York", departure_date="2026-02-22"
        )
        result = transport_tool(req)
        assert isinstance(result, ToolError)
        assert result.type == "validation"

    def test_validation_error_on_bad_date(self) -> None:
        req = TransportSearchRequest(
            origin="Chicago", destination="New York", departure_date="not-a-date"
        )
        result = transport_tool(req)
        assert isinstance(result, ToolError)
        assert result.type == "validation"

    def test_max_results_respected(self) -> None:
        req = TransportSearchRequest(
            origin="Chicago",
            destination="New York",
            departure_date="2026-02-22",
            max_results=2,
        )
        result = transport_tool(req)
        assert not isinstance(result, ToolError)
        assert len(result.options) <= 2
