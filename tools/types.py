from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ToolErrorType = Literal[
    "timeout",
    "no_results",
    "not_found",
    "rate_limited",
    "validation",
    "auth",
    "unknown",
]


class ToolError(BaseModel):
    type: ToolErrorType
    message: str
    retryable: bool = False


class ToolCallEnvelope(BaseModel):
    tool_name: str
    args: dict[str, Any]
    result: dict[str, Any] | None = None
    error: ToolError | None = None


class SearchRequest(BaseModel):
    query: str
    filters: dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str


class SearchResponse(BaseModel):
    results: list[SearchResult]


class MapsRequest(BaseModel):
    origin: str
    destination: str
    mode: Literal["driving", "walking", "transit"] = "driving"


class MapsResponse(BaseModel):
    distance_km: float
    duration_min: int


class CalendarRequest(BaseModel):
    title: str
    start_iso: str
    end_iso: str
    location: str | None = None


class CalendarResponse(BaseModel):
    event_id: str


class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str


class EmailResponse(BaseModel):
    message_id: str


# ---------------------------------------------------------------------------
# Transport search (flights, trains, buses)
# ---------------------------------------------------------------------------

TransportMode = Literal["flight", "train", "bus", "any"]


class TransportSearchRequest(BaseModel):
    """Search for transport options between two places."""

    origin: str
    destination: str
    departure_date: str  # YYYY-MM-DD
    mode: TransportMode = "any"
    max_results: int = 5


class TransportOption(BaseModel):
    option_id: str
    mode: TransportMode
    carrier: str
    departure_iso: str
    arrival_iso: str
    duration_min: int
    price_usd: float
    stops: int = 0
    booking_url: str


class TransportSearchResponse(BaseModel):
    origin: str
    destination: str
    options: list[TransportOption]  # sorted by price ascending
