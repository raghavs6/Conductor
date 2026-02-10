from tools.mocks import calendar_tool, search_tool
from tools.types import CalendarRequest, SearchRequest, ToolError


def test_search_mock_deterministic() -> None:
    request = SearchRequest(query="best ramen")
    first = search_tool(request)
    second = search_tool(request)
    assert first == second


def test_calendar_validation_error() -> None:
    request = CalendarRequest(title="", start_iso="", end_iso="")
    result = calendar_tool(request)
    assert isinstance(result, ToolError)
    assert result.type == "validation"
