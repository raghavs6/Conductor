from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    name: str
    message: str
    expected_tools: list[str]


SCENARIOS: list[Scenario] = [
    # -----------------------------------------------------------------------
    # Original scenarios (kept for backward compatibility)
    # -----------------------------------------------------------------------
    Scenario(
        scenario_id="hotel_email_summary",
        name="Find hotel and email summary",
        message="Find a hotel in Boston and email me a summary.",
        expected_tools=["search_gmail"],
    ),
    Scenario(
        scenario_id="route_calendar",
        name="Plan route and add to calendar",
        message="Plan a route to the museum and add it to my calendar.",
        expected_tools=["read_calendar"],
    ),
    Scenario(
        scenario_id="cheaper_compare",
        name="Cheaper option compare",
        message="Search for a cheaper option and compare results.",
        expected_tools=["search_transport"],
    ),
    # -----------------------------------------------------------------------
    # New travel scenarios
    # -----------------------------------------------------------------------
    Scenario(
        scenario_id="flight_search",
        name="Find a flight from Chicago to NYC",
        message="Find me a flight from Chicago to New York next Friday.",
        expected_tools=["read_calendar", "search_gmail", "search_transport"],
    ),
    Scenario(
        scenario_id="train_with_calendar",
        name="Train to Boston with calendar check",
        message="Check my calendar and find a train to Boston on Saturday.",
        expected_tools=["read_calendar", "search_transport"],
    ),
    Scenario(
        scenario_id="email_confirmation_search",
        name="Search for flight confirmation emails",
        message="Do I have any flight confirmation emails in my inbox?",
        expected_tools=["search_gmail"],
    ),
]
