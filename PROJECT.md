# AI Assistant (Tools + Multimodal + Evals)

## Goal

Build an AI assistant that can understand complex user requests, decompose them into multiple steps, call external tools, verify results, handle follow-ups, support multimodal inputs (images/files), and improve over time via automated evaluations.

## Development setup

- Install dependencies: `pip install -r requirements-dev.txt`
- Run tests: `python -m pytest -q`

## Example user requests

- “Plan my trip and book it.”
- “Here’s a screenshot of my itinerary—add it to my calendar and email it to me.”
- “Find a cheaper hotel near the same area, but keep it refundable.”

## Core capabilities

1. **Task decomposition**: Convert a request into a step plan (task graph).
2. **Tool calling**: Call multiple external tools (search, booking, calendar/email, maps).
3. **Verification**: Validate tool results vs constraints; detect inconsistencies and re-plan.
4. **Follow-ups**: Persist structured state so edits don’t restart the whole process.
5. **Multimodal**: Accept images/files; extract structured facts with confidence + provenance.
6. **Traces**: Log step-by-step traces (plan, tool calls, verifier checks, outcomes).
7. **Automated evals**: Scenario-based tests + scoring to measure improvements over time.

## Safety / high-stakes rules

- No purchases/bookings without explicit confirmation (“two-phase commit”: draft/hold → confirm → commit).
- Always show a summary of what will happen before committing.
- Handle tool failures and price/availability changes safely.

## Architecture (MVP)

- FastAPI backend
- Agent runtime: Plan → Execute → Verify loop
- Tool interface: typed inputs/outputs + error taxonomy + timeouts/retries
- TripState (structured state): requirements, candidates, decisions, booking status, audit log
- Tracing: JSONL per run
- Eval harness: deterministic scenarios with tool mocks + scoring rubric

## MVP scope (phase 1)

- Build planning + tool orchestration using **mock tools** (no real bookings/payment yet).
- Traces + eval suite runs locally and in CI.

## Folder layout (target)

- app/ # FastAPI entrypoints
- agent/ # orchestrator, planning/execution/verification
- tools/ # tool interface + mocks
- eval/ # scenarios + scoring + runner
- tests/ # pytest
- docs/ # extra design notes
