"""Transport search tool (flights, trains, buses) — mock + real-API stub.

Set USE_REAL_TRANSPORT_API=1 in your .env (plus AVIATIONSTACK_API_KEY)
to switch to the live AviationStack API for flights.
Train/bus real APIs can be wired in similarly.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta, timezone

try:
    import requests  # type: ignore[import]
except ImportError:
    requests = None  # type: ignore[assignment]

from .types import (
    TransportOption,
    TransportSearchRequest,
    TransportSearchResponse,
    ToolError,
)


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Mock implementation (deterministic, no network calls)
# ---------------------------------------------------------------------------


def _mock_transport(
    payload: TransportSearchRequest,
) -> TransportSearchResponse | ToolError:
    if not payload.origin.strip() or not payload.destination.strip():
        return ToolError(
            type="validation",
            message="origin and destination are required",
            retryable=False,
        )
    if not payload.departure_date.strip():
        return ToolError(
            type="validation",
            message="departure_date is required (YYYY-MM-DD)",
            retryable=False,
        )

    try:
        dep_date = datetime.strptime(payload.departure_date, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return ToolError(
            type="validation",
            message="departure_date must be YYYY-MM-DD",
            retryable=False,
        )

    origin = payload.origin.strip()
    destination = payload.destination.strip()
    mode_filter = payload.mode  # "flight", "train", "bus", or "any"

    # Build deterministic mock options
    seed = f"{origin}:{destination}:{payload.departure_date}"

    all_options: list[TransportOption] = []

    if mode_filter in ("flight", "any"):
        dep = dep_date.replace(hour=8, minute=0)
        arr = dep + timedelta(hours=2, minutes=30)
        all_options.append(
            TransportOption(
                option_id=_stable_id(seed + ":flight:1"),
                mode="flight",
                carrier="MockAir",
                departure_iso=dep.isoformat(),
                arrival_iso=arr.isoformat(),
                duration_min=150,
                price_usd=round(189.99 + len(origin) * 2.5, 2),
                stops=0,
                booking_url=f"https://mockair.example.com/book?from={origin}&to={destination}&date={payload.departure_date}",
            )
        )
        dep2 = dep_date.replace(hour=14, minute=30)
        arr2 = dep2 + timedelta(hours=3, minutes=45)
        all_options.append(
            TransportOption(
                option_id=_stable_id(seed + ":flight:2"),
                mode="flight",
                carrier="BudgetJet",
                departure_iso=dep2.isoformat(),
                arrival_iso=arr2.isoformat(),
                duration_min=225,
                price_usd=round(129.00 + len(destination) * 1.5, 2),
                stops=1,
                booking_url=f"https://budgetjet.example.com/book?from={origin}&to={destination}&date={payload.departure_date}",
            )
        )

    if mode_filter in ("train", "any"):
        dep = dep_date.replace(hour=7, minute=45)
        arr = dep + timedelta(hours=5, minutes=0)
        all_options.append(
            TransportOption(
                option_id=_stable_id(seed + ":train:1"),
                mode="train",
                carrier="MockRail",
                departure_iso=dep.isoformat(),
                arrival_iso=arr.isoformat(),
                duration_min=300,
                price_usd=round(89.00 + len(origin) * 1.0, 2),
                stops=0,
                booking_url=f"https://mockrail.example.com/book?from={origin}&to={destination}&date={payload.departure_date}",
            )
        )

    if mode_filter in ("bus", "any"):
        dep = dep_date.replace(hour=22, minute=0)
        arr = dep + timedelta(hours=9, minutes=30)
        all_options.append(
            TransportOption(
                option_id=_stable_id(seed + ":bus:1"),
                mode="bus",
                carrier="MockHound",
                departure_iso=dep.isoformat(),
                arrival_iso=arr.isoformat(),
                duration_min=570,
                price_usd=round(49.00 + len(destination) * 0.5, 2),
                stops=2,
                booking_url=f"https://mockhound.example.com/book?from={origin}&to={destination}&date={payload.departure_date}",
            )
        )

    # Sort by price ascending, cap at max_results
    all_options.sort(key=lambda o: o.price_usd)
    return TransportSearchResponse(
        origin=origin,
        destination=destination,
        options=all_options[: payload.max_results],
    )


# ---------------------------------------------------------------------------
# Real-API implementation (only active when USE_REAL_TRANSPORT_API=1)
# ---------------------------------------------------------------------------


def _real_transport(
    payload: TransportSearchRequest,
) -> TransportSearchResponse | ToolError:
    """AviationStack flight search API."""
    if requests is None:
        return ToolError(
            type="unknown",
            message="requests not installed. Run: pip install requests",
            retryable=False,
        )

    api_key = os.environ.get("AVIATIONSTACK_API_KEY", "")
    if not api_key:
        return ToolError(
            type="auth",
            message="AVIATIONSTACK_API_KEY is not set",
            retryable=False,
        )

    origin = payload.origin.strip()
    destination = payload.destination.strip()

    try:
        resp = requests.get(
            "http://api.aviationstack.com/v1/flights",
            params={
                "access_key": api_key,
                "dep_iata": origin,
                "arr_iata": destination,
                "flight_date": payload.departure_date,
                "limit": payload.max_results,
                "flight_status": "scheduled",
            },
            timeout=15,
        )
    except requests.exceptions.Timeout:
        return ToolError(
            type="timeout", message="AviationStack request timed out", retryable=True
        )
    except requests.exceptions.RequestException as exc:
        return ToolError(type="unknown", message=str(exc), retryable=True)

    if not resp.ok:
        if resp.status_code == 401:
            return ToolError(
                type="auth",
                message="AviationStack auth failed — check AVIATIONSTACK_API_KEY",
                retryable=False,
            )
        return ToolError(
            type="unknown",
            message=f"AviationStack error: {resp.status_code}",
            retryable=True,
        )

    data = resp.json().get("data", [])
    if not data:
        return ToolError(
            type="no_results",
            message="No flights found for that route/date",
            retryable=False,
        )

    options: list[TransportOption] = []
    for flight in data:
        dep_str = (flight.get("departure") or {}).get("scheduled")
        arr_str = (flight.get("arrival") or {}).get("scheduled")
        if not dep_str or not arr_str:
            continue

        try:
            dep_dt = datetime.fromisoformat(dep_str)
            arr_dt = datetime.fromisoformat(arr_str)
        except ValueError:
            continue

        duration_min = (arr_dt - dep_dt).total_seconds() / 60
        if duration_min <= 0:
            continue

        flight_iata = (flight.get("flight") or {}).get(
            "iata"
        ) or f"{origin}{destination}"
        carrier = (flight.get("airline") or {}).get("name") or "Unknown"

        # Deterministic mock price: ~$190–$240 range with per-flight variation via hash
        price_usd = round(
            189.99
            + len(origin) * 2.5
            + (int(_stable_id(flight_iata)[:4], 16) % 100) * 0.5,
            2,
        )

        options.append(
            TransportOption(
                option_id=_stable_id(flight_iata),
                mode="flight",
                carrier=carrier,
                departure_iso=dep_str,
                arrival_iso=arr_str,
                duration_min=int(duration_min),
                price_usd=price_usd,
                stops=0,
                booking_url=f"https://www.google.com/flights#flt={origin}.{destination}.{payload.departure_date}",
            )
        )

    if not options:
        return ToolError(
            type="no_results",
            message="No valid flight records in response",
            retryable=False,
        )

    options.sort(key=lambda o: o.price_usd)
    return TransportSearchResponse(
        origin=origin,
        destination=destination,
        options=options,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def transport_tool(
    payload: TransportSearchRequest,
) -> TransportSearchResponse | ToolError:
    if os.environ.get("USE_REAL_TRANSPORT_API") == "1":
        return _real_transport(payload)
    return _mock_transport(payload)
