"""Multi-step travel planner.

Given a user message, `build_plan` returns an ordered list of
`TravelPlanStep` objects that the agent loop will execute in sequence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any


@dataclass
class TravelPlanStep:
    tool_name: str
    args: dict[str, Any] = field(default_factory=dict)
    description: str = ""


# ---------------------------------------------------------------------------
# Keyword helpers
# ---------------------------------------------------------------------------

_FLIGHT_KW = {"flight", "fly", "plane", "airline", "airport"}
_TRAIN_KW = {"train", "rail", "amtrak", "railway"}
_BUS_KW = {"bus", "greyhound", "coach"}


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", text.lower()))


def _detect_mode(words: set[str]) -> str:
    if words & _FLIGHT_KW:
        return "flight"
    if words & _TRAIN_KW:
        return "train"
    if words & _BUS_KW:
        return "bus"
    return "any"


def _detect_date(message: str) -> str:
    """Extract a YYYY-MM-DD date from the message, or default to next Friday."""
    # Look for explicit YYYY-MM-DD
    m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", message)
    if m:
        return m.group(1)

    today = datetime.now(timezone.utc)

    # "next <weekday>"
    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    m2 = re.search(r"\bnext\s+(\w+)\b", message.lower())
    if m2 and m2.group(1) in weekdays:
        target = weekdays[m2.group(1)]
        days_ahead = (target - today.weekday() + 7) % 7 or 7
        return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    # "this <weekday>"
    m3 = re.search(r"\bthis\s+(\w+)\b", message.lower())
    if m3 and m3.group(1) in weekdays:
        target = weekdays[m3.group(1)]
        days_ahead = (target - today.weekday()) % 7
        return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    # "on <weekday>" or bare weekday
    m4 = re.search(r"\bon\s+(\w+)\b", message.lower()) or re.search(
        r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        message.lower(),
    )
    if m4:
        day_word = m4.group(1)
        if day_word in weekdays:
            target = weekdays[day_word]
            days_ahead = (target - today.weekday() + 7) % 7 or 7
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    # Default: next Friday
    days_ahead = (4 - today.weekday() + 7) % 7 or 7
    return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")


def _detect_locations(message: str) -> tuple[str, str]:
    """Very simple origin/destination extraction.

    Looks for patterns like:
      "from X to Y"
      "X to Y"
      "to Y from X"
    Falls back to generic placeholders so the tool can still run.
    """
    msg = message

    # "from X to Y"
    m = re.search(
        r"\bfrom\s+([A-Za-z ,]+?)\s+to\s+([A-Za-z ,]+?)(?:\s+on|\s+next|\s+this|\s+by|$)",
        msg,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).strip(), m.group(2).strip()

    # "to Y from X"
    m2 = re.search(
        r"\bto\s+([A-Za-z ,]+?)\s+from\s+([A-Za-z ,]+?)(?:\s+on|\s+next|\s+this|\s+by|$)",
        msg,
        re.IGNORECASE,
    )
    if m2:
        return m2.group(2).strip(), m2.group(1).strip()

    # "to Y" only
    m3 = re.search(
        r"\bto\s+([A-Za-z ,]+?)(?:\s+on|\s+next|\s+this|\s+by|$)", msg, re.IGNORECASE
    )
    if m3:
        return "Current Location", m3.group(1).strip()

    return "Origin", "Destination"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_plan(message: str) -> list[TravelPlanStep]:
    """Return an ordered list of steps to execute for the given user message."""
    words = _words(message)
    steps: list[TravelPlanStep] = []

    wants_transport = bool(
        words & _FLIGHT_KW | words & _TRAIN_KW | words & _BUS_KW
        or any(
            kw in message.lower()
            for kw in ("find me", "search", "look for", "get me", "book")
        )
    )

    # Step 1 — search for transport options
    if wants_transport:
        origin, destination = _detect_locations(message)
        dep_date = _detect_date(message)
        mode = _detect_mode(words)
        steps.append(
            TravelPlanStep(
                tool_name="search_transport",
                args={
                    "origin": origin,
                    "destination": destination,
                    "departure_date": dep_date,
                    "mode": mode,
                    "max_results": 5,
                },
                description=f"Search {mode} options from {origin} to {destination} on {dep_date}",
            )
        )

    # Fallback — if nothing matched, do a generic search
    if not steps:
        steps.append(
            TravelPlanStep(
                tool_name="search",
                args={"query": message},
                description="General web search",
            )
        )

    return steps
