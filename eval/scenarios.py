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
        scenario_id="cheaper_compare",
        name="Cheaper option compare",
        message="Search for a cheaper option and compare results.",
        expected_tools=["search_transport"],
    ),
    Scenario(
        scenario_id="flight_search",
        name="Find a flight from Chicago to NYC",
        message="Find me a flight from Chicago to New York next Friday.",
        expected_tools=["search_transport"],
    ),
    Scenario(
        scenario_id="train_with_calendar",
        name="Train to Boston",
        message="Check my calendar and find a train to Boston on Saturday.",
        expected_tools=["search_transport"],
    ),
]
