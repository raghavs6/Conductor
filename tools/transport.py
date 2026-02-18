"""Transport search tool (flights, trains, buses) — mock + real-API stub.

Set USE_REAL_TRANSPORT_API=1 in your .env (plus AMADEUS_CLIENT_ID,
AMADEUS_CLIENT_SECRET) to switch to the live Amadeus API for flights.
Train/bus real APIs can be wired in similarly.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta, timezone

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
# Real-API stub (only active when USE_REAL_TRANSPORT_API=1)
# ---------------------------------------------------------------------------


def _real_transport(
    payload: TransportSearchRequest,
) -> TransportSearchResponse | ToolError:  # pragma: no cover
    """Stub for real Amadeus flight search API."""
    try:
        import requests  # type: ignore
    except ImportError:
        return ToolError(
            type="unknown",
            message="requests not installed. Run: pip install requests",
            retryable=False,
        )

    # 1. Get access token
    token_resp = requests.post(
        "https://test.api.amadeus.com/v1/security/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": os.environ.get("AMADEUS_CLIENT_ID", ""),
            "client_secret": os.environ.get("AMADEUS_CLIENT_SECRET", ""),
        },
        timeout=10,
    )
    if not token_resp.ok:
        return ToolError(type="auth", message="Amadeus auth failed", retryable=True)
    access_token = token_resp.json().get("access_token", "")

    # 2. Search flights (IATA codes required for real API)
    search_resp = requests.get(
        "https://test.api.amadeus.com/v2/shopping/flight-offers",
        headers={"Authorization": f"Bearer {access_token}"},
        params={
            "originLocationCode": payload.origin,
            "destinationLocationCode": payload.destination,
            "departureDate": payload.departure_date,
            "adults": 1,
            "max": payload.max_results,
            "currencyCode": "USD",
        },
        timeout=15,
    )
    if not search_resp.ok:
        return ToolError(
            type="unknown",
            message=f"Amadeus search error: {search_resp.status_code}",
            retryable=True,
        )

    offers = search_resp.json().get("data", [])
    options: list[TransportOption] = []
    for offer in offers:
        seg = offer["itineraries"][0]["segments"][0]
        options.append(
            TransportOption(
                option_id=offer["id"],
                mode="flight",
                carrier=seg["carrierCode"],
                departure_iso=seg["departure"]["at"],
                arrival_iso=seg["arrival"]["at"],
                duration_min=int(
                    offer["itineraries"][0]["duration"]
                    .replace("PT", "")
                    .replace("H", "*60+")
                    .replace("M", "")
                    .split("+")[0]
                )
                * 60
                + int(
                    offer["itineraries"][0]["duration"]
                    .replace("PT", "")
                    .replace("H", "*60+")
                    .replace("M", "")
                    .split("+")[1]
                    or 0
                ),
                price_usd=float(offer["price"]["total"]),
                stops=len(offer["itineraries"][0]["segments"]) - 1,
                booking_url="https://amadeus.com",
            )
        )
    options.sort(key=lambda o: o.price_usd)
    return TransportSearchResponse(
        origin=payload.origin,
        destination=payload.destination,
        options=options,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def transport_tool(
    payload: TransportSearchRequest,
) -> TransportSearchResponse | ToolError:
    if os.environ.get("USE_REAL_TRANSPORT_API") == "1":
        return _real_transport(payload)  # pragma: no cover
    return _mock_transport(payload)
