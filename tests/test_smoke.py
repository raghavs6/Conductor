from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_chat() -> None:
    resp = client.post("/chat", json={"message": "hi"})
    assert resp.status_code == 200
    assert resp.json() == {"reply": "You said: hi"}
