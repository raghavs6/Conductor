from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent.run import InMemoryStateStore, TraceSink, run_chat
from agent.types import TraceEvent

from .scenarios import SCENARIOS
from .scoring import score_tool_calls


class InMemoryTraceSink(TraceSink):
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def emit(self, event: TraceEvent) -> None:
        self.events.append(event.model_dump())


def run_evals(output_path: Path | str = Path("eval/results.json")) -> dict[str, Any]:
    results: list[dict[str, Any]] = []

    for scenario in SCENARIOS:
        state_store = InMemoryStateStore()
        trace_sink = InMemoryTraceSink()
        reply = run_chat(
            scenario.message, state_store=state_store, trace_sink=trace_sink
        )
        score = score_tool_calls(trace_sink.events, scenario.expected_tools)

        results.append(
            {
                "scenario_id": scenario.scenario_id,
                "name": scenario.name,
                "message": scenario.message,
                "expected_tools": scenario.expected_tools,
                "passed": score.passed,
                "reasons": score.reasons,
                "tool_calls": score.tool_calls,
                "reply": reply,
            }
        )

    report = {
        "summary": {
            "total": len(results),
            "passed": sum(result["passed"] for result in results),
            "failed": sum(not result["passed"] for result in results),
        },
        "results": results,
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=True))

    return report


def main() -> None:
    report = run_evals()
    summary = report["summary"]
    print(
        f"Eval results: {summary['passed']}/{summary['total']} passed, {summary['failed']} failed"
    )
    for result in report["results"]:
        status = "PASS" if result["passed"] else "FAIL"
        print(f"[{status}] {result['scenario_id']}: {result['name']}")
        for reason in result["reasons"]:
            print(f"  - {reason}")


if __name__ == "__main__":
    main()
