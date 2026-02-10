# Codex Working Agreement

## Non-negotiables

- Make SMALL, incremental changes. Do not rewrite architecture without updating PROJECT.md.
- Always add or update pytest tests for new behavior.
- Always run: `python -m pytest -q` before finishing a task.
- If tests fail, fix them. Do not leave the repo red.
- Never commit secrets. Use `.env` locally and `.env.example` in repo.

## Output requirements

- Prefer returning a unified diff (patch) when asked.
- Keep changes scoped to the ticket.
- Use typed Pydantic models for state and tool I/O.

## Safety requirements

- Any “booking/payment/commit” action must use two-phase commit:
  1. draft/quote/hold + summarize
  2. require explicit user confirmation to commit

## Quality bar

- Deterministic evals: tests must not depend on live web calls.
- All tool calls must be logged in traces (redact sensitive fields).

## I am a beginer coder

- Do not let me over use my AWS or CODEX rates so I have to pay extra money
