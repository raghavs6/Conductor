import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app import main as app_main


client = TestClient(app)


def test_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_chat() -> None:
    traces_dir = Path("traces")
    traces_dir.mkdir(parents=True, exist_ok=True)
    before = set(traces_dir.glob("*.jsonl"))
    before_count = app_main.STATE_STORE.count()

    resp = client.post("/chat", json={"message": "hi"})
    assert resp.status_code == 200
    assert "reply" in resp.json()

    after = set(traces_dir.glob("*.jsonl"))
    new_files = after - before
    assert len(new_files) == 1
    assert app_main.STATE_STORE.count() == before_count + 1

    trace_path = next(iter(new_files))
    with trace_path.open("r", encoding="utf-8") as f:
        events = [json.loads(line) for line in f if line.strip()]
    event_types = {event["type"] for event in events}
    assert "request_received" in event_types
    assert "tool_called" in event_types


def test_chat_travel_intent() -> None:
    """A travel-intent message should trigger search_transport in the trace."""
    traces_dir = Path("traces")
    traces_dir.mkdir(parents=True, exist_ok=True)
    before = set(traces_dir.glob("*.jsonl"))

    resp = client.post(
        "/chat",
        json={"message": "Find me a flight from Chicago to New York next Friday"},
    )
    assert resp.status_code == 200
    reply = resp.json()["reply"]
    assert (
        "Chicago" in reply
        or "New York" in reply
        or "transport" in reply.lower()
        or "✈" in reply
    )

    after = set(traces_dir.glob("*.jsonl"))
    new_files = after - before
    assert len(new_files) == 1

    trace_path = next(iter(new_files))
    with trace_path.open("r", encoding="utf-8") as f:
        events = [json.loads(line) for line in f if line.strip()]

    tool_names = [
        e["payload"].get("tool_name") for e in events if e.get("type") == "tool_called"
    ]
    assert "search_transport" in tool_names
