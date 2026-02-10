# MM AI Agent

A FastAPI-based AI assistant skeleton with an agent loop, deterministic mock tools, traces, and tests.

## Quickstart

Install deps:

```bash
pip install -r requirements-dev.txt
```

Run the app:

```bash
uvicorn app.main:app --reload
```

Open API docs:

- `http://127.0.0.1:8000/docs`

## Endpoints

- `GET /health` → `{ "status": "ok" }`
- `POST /chat` → `{ "reply": "You said: ..." }`

Example:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"hi"}'
```

## Docker

Build:

```bash
docker build -t mm-ai-agent .
```

Run:

```bash
docker run --rm -p 8000:8000 mm-ai-agent
```

## Traces

Each `/chat` request emits JSONL trace events under `traces/` (one file per request). The trace sink is swappable.

## Tests

```bash
python -m pytest -q
```

## Tool Mocks

Deterministic mock tools for `search`, `maps`, `calendar`, and `email` live in `tools/` and are used by the agent loop.

## Pre-commit

```bash
pre-commit run --all-files
```
