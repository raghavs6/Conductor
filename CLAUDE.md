## Non-negotiables

- Make SMALL, incremental changes. Do not rewrite architecture without updating PROJECT.md.
- Always add or update pytest tests for new behavior.
- Always run: `python -m pytest -q` before finishing a task.
- If tests fail, fix them. Do not leave the repo red.
- Never commit secrets. Use `.env` locally and `.env.example` in repo.
- This repo uses .gitignore. Do not add ignored files or suggest committing them.

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

Review this plan thoroughly before making any code changes. For every issue or recommendation, explain the concrete tradeoffs, give me an opinionated recommendation, and ask for my input before assuming a direction.
My engineering preferences (use these to guide your recommendations):
DRY is important-flag repetition aggressively.
Well-tested code is non-negotiable; I'd rather have too many tests than too few.
I want code that's "engineered enough" - not under-engineered (fragile, hacky) and not over-engineered (premature abstraction, unnecessary complexity).
I err on the side of handling more edge cases, not fewer; thoughtfulness > speed.
Bias toward explicit over clever.

1. Architecture review
   Evaluate:
   Overall system design and component boundaries.
   Dependency graph and coupling concerns.
   Data flow patterns and potential bottlenecks.
   Scaling characteristics and single points of failure.
   Security architecture (auth, data access, API boundaries).
2. Code quality review
   Evaluate:
   Code organization and module structure.
   DRY violations-be aggressive here.
   Error handling patterns and missing edge cases (call these out explicitly).
   Technical debt hotspots.
   Areas that are over-engineered or under-engineered relative to my preferences.
3. Test review
   Evaluate:
   Test coverage gaps (unit, integration, e2e).
   Test quality and assertion strength.
   Missing edge case coverage-be thorough.
   Untested failure modes and error paths.
4. Performance review
   Evaluate:
   N+1 queries and database access patterns.
   Memory-usage concerns.
   Caching opportunities.
   Slow or high-complexity code paths.
   For each issue you find
   For every specific issue (bug, smell, design concern, or risk):
   Describe the problem concretely, with file and line references.
   Present 2-3 options, including "do nothing" where that's reasonable.
   For each option, specify: implementation effort, risk, impact on other code, and maintenance burden.
   Give me your recommended option and why, mapped to my preferences above.
   Then explicitly ask whether I agree or want to choose a different direction before proceeding.
   Workflow and interaction
   Do not assume my priorities on timeline or scale.
   After each section, pause and ask for my feedback before moving on.
   BEFORE YOU START:
   Ask if I want one of two options:
   1/ BIG CHANGE: Work through this interactively, one section at a time (Architecture → Code Quality → Tests → Performance) with at most 4 top issues in each
   section.
   2/ SMALL CHANGE: Work through interactively ONE question per review section
   FOR EACH STAGE OF REVIEW: output the explanation and pros and cons of each stage's questions AND your opinionated recommendation and why, and then use AskUserQuestion. Also NUMBER issues and then give LETTERS for options and when using AskUserQuestion make sure each option clearly labels the issue NUMBER and option LETTER so the user doesn't get confused. Make the recommended option always the 1st option.
