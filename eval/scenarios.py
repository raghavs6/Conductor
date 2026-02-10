from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    name: str
    message: str
    expected_tools: list[str]


SCENARIOS: list[Scenario] = [
    Scenario(
        scenario_id="hotel_email_summary",
        name="Find hotel and email summary",
        message="Find a hotel in Boston and email me a summary.",
        expected_tools=["email"],
    ),
    Scenario(
        scenario_id="route_calendar",
        name="Plan route and add to calendar",
        message="Plan a route to the museum and add it to my calendar.",
        expected_tools=["calendar"],
    ),
    Scenario(
        scenario_id="cheaper_compare",
        name="Cheaper option compare",
        message="Search for a cheaper option and compare results.",
        expected_tools=["search"],
    ),
]
