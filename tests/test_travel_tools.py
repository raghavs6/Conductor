"""Tests for the transport tool."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

from tools.transport import transport_tool
from tools.types import (
    TransportSearchRequest,
    TransportSearchResponse,
    ToolError,
)


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


# ---------------------------------------------------------------------------
# Transport — real AviationStack API (mocked HTTP)
# ---------------------------------------------------------------------------


class TestTransportReal:
    """Tests for AviationStack real-API path using mocked HTTP."""

    FAKE_RESPONSE = {
        "pagination": {"count": 1},
        "data": [
            {
                "departure": {"scheduled": "2026-03-01T08:00:00+00:00"},
                "arrival": {"scheduled": "2026-03-01T11:30:00+00:00"},
                "airline": {"name": "Test Airlines"},
                "flight": {"iata": "TS100"},
            }
        ],
    }

    def _make_mock_resp(self, ok=True, json_data=None, status_code=200):
        m = MagicMock()
        m.ok = ok
        m.status_code = status_code
        m.json.return_value = json_data or self.FAKE_RESPONSE
        return m

    def test_parses_flight_correctly(self):
        with patch("tools.transport.requests") as mock_req, patch.dict(
            os.environ,
            {"USE_REAL_TRANSPORT_API": "1", "AVIATIONSTACK_API_KEY": "test_key"},
        ):
            mock_req.get.return_value = self._make_mock_resp()
            mock_req.exceptions.Timeout = Exception
            mock_req.exceptions.RequestException = Exception
            req = TransportSearchRequest(
                origin="ORD", destination="JFK", departure_date="2026-03-01"
            )
            result = transport_tool(req)
        assert isinstance(result, TransportSearchResponse)
        assert len(result.options) == 1
        opt = result.options[0]
        assert opt.carrier == "Test Airlines"
        assert opt.duration_min == 210  # 3.5 hours
        assert opt.mode == "flight"
        assert opt.price_usd > 0

    def test_auth_error_on_missing_key(self):
        env = {"USE_REAL_TRANSPORT_API": "1"}
        with patch("tools.transport.requests") as mock_req, patch.dict(
            os.environ, env, clear=False
        ):
            mock_req.exceptions.Timeout = Exception
            mock_req.exceptions.RequestException = Exception
            os.environ.pop("AVIATIONSTACK_API_KEY", None)
            req = TransportSearchRequest(
                origin="ORD", destination="JFK", departure_date="2026-03-01"
            )
            result = transport_tool(req)
        assert isinstance(result, ToolError)
        assert result.type == "auth"

    def test_no_results_error_on_empty_data(self):
        with patch("tools.transport.requests") as mock_req, patch.dict(
            os.environ,
            {"USE_REAL_TRANSPORT_API": "1", "AVIATIONSTACK_API_KEY": "test_key"},
        ):
            mock_req.get.return_value = self._make_mock_resp(
                json_data={"pagination": {"count": 0}, "data": []}
            )
            mock_req.exceptions.Timeout = Exception
            mock_req.exceptions.RequestException = Exception
            req = TransportSearchRequest(
                origin="ORD", destination="JFK", departure_date="2026-03-01"
            )
            result = transport_tool(req)
        assert isinstance(result, ToolError)
        assert result.type == "no_results"

    def test_http_401_returns_auth_error(self):
        with patch("tools.transport.requests") as mock_req, patch.dict(
            os.environ,
            {"USE_REAL_TRANSPORT_API": "1", "AVIATIONSTACK_API_KEY": "bad_key"},
        ):
            mock_req.get.return_value = self._make_mock_resp(ok=False, status_code=401)
            mock_req.exceptions.Timeout = Exception
            mock_req.exceptions.RequestException = Exception
            req = TransportSearchRequest(
                origin="ORD", destination="JFK", departure_date="2026-03-01"
            )
            result = transport_tool(req)
        assert isinstance(result, ToolError)
        assert result.type == "auth"
        assert result.retryable is False
