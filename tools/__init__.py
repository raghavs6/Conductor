from .calendar_google import calendar_google_tool
from .calendar_outlook import calendar_outlook_tool
from .gmail import gmail_tool
from .mocks import TOOL_REGISTRY
from .transport import transport_tool
from .types import (
    CalendarEvent,
    CalendarReadRequest,
    CalendarReadResponse,
    CalendarRequest,
    CalendarResponse,
    EmailMessage,
    EmailRequest,
    EmailResponse,
    EmailSearchRequest,
    EmailSearchResponse,
    MapsRequest,
    MapsResponse,
    SearchRequest,
    SearchResponse,
    ToolCallEnvelope,
    ToolError,
    ToolErrorType,
    TransportOption,
    TransportSearchRequest,
    TransportSearchResponse,
)

__all__ = [
    # Registry
    "TOOL_REGISTRY",
    # Tool functions
    "calendar_google_tool",
    "calendar_outlook_tool",
    "gmail_tool",
    "transport_tool",
    # Types — legacy
    "CalendarRequest",
    "CalendarResponse",
    "EmailRequest",
    "EmailResponse",
    "MapsRequest",
    "MapsResponse",
    "SearchRequest",
    "SearchResponse",
    "ToolCallEnvelope",
    "ToolError",
    "ToolErrorType",
    # Types — new
    "CalendarEvent",
    "CalendarReadRequest",
    "CalendarReadResponse",
    "EmailMessage",
    "EmailSearchRequest",
    "EmailSearchResponse",
    "TransportOption",
    "TransportSearchRequest",
    "TransportSearchResponse",
]
