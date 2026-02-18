from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from agent.run import InMemoryStateStore, JsonlTraceSink, run_chat

app = FastAPI(title="MM AI Agent — Travel Assistant")

STATE_STORE = InMemoryStateStore()
TRACE_SINK = JsonlTraceSink(traces_dir=Path("traces"))


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    reply = run_chat(payload.message, state_store=STATE_STORE, trace_sink=TRACE_SINK)
    return ChatResponse(reply=reply)


# ---------------------------------------------------------------------------
# OAuth stubs — wire up real flows when you have credentials in .env
# ---------------------------------------------------------------------------


@app.get("/auth/google")
def auth_google() -> dict:
    """
    Stub: In production, redirect the user to Google's OAuth2 consent screen.
    Required env vars: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
    Scopes needed: https://www.googleapis.com/auth/calendar.readonly
                   https://www.googleapis.com/auth/gmail.readonly
    """
    return {
        "status": "stub",
        "message": "Set USE_REAL_GOOGLE_API=1 and supply GOOGLE_CLIENT_ID, "
        "GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN in .env to enable.",
    }


@app.get("/auth/google/callback")
def auth_google_callback(code: str = "") -> dict:
    """Stub: Exchange auth code for tokens and store in TOKEN_STORE."""
    return {"status": "stub", "code_received": bool(code)}


@app.get("/auth/outlook")
def auth_outlook() -> dict:
    """
    Stub: In production, redirect the user to Microsoft's OAuth2 consent screen.
    Required env vars: OUTLOOK_CLIENT_ID, OUTLOOK_CLIENT_SECRET, OUTLOOK_TENANT_ID
    Scopes needed: Calendars.Read
    """
    return {
        "status": "stub",
        "message": "Set USE_REAL_OUTLOOK_API=1 and supply OUTLOOK_CLIENT_ID, "
        "OUTLOOK_CLIENT_SECRET, OUTLOOK_TENANT_ID, OUTLOOK_REFRESH_TOKEN in .env to enable.",
    }


@app.get("/auth/outlook/callback")
def auth_outlook_callback(code: str = "") -> dict:
    """Stub: Exchange auth code for tokens and store in TOKEN_STORE."""
    return {"status": "stub", "code_received": bool(code)}
