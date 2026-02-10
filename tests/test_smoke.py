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
    assert resp.json() == {"reply": "You said: hi"}

    after = set(traces_dir.glob("*.jsonl"))
    new_files = after - before
    assert len(new_files) == 1
    assert app_main.STATE_STORE.count() == before_count + 1

    trace_path = next(iter(new_files))
    with trace_path.open("r", encoding="utf-8") as f:
        first_event = json.loads(f.readline())
    assert first_event["type"] == "request_received"
