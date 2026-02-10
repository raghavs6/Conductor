from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from agent.run import InMemoryStateStore, JsonlTraceSink, run_chat

app = FastAPI(title="MM AI Agent")

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
