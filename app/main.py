from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="MM AI Agent")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    reply = f"You said: {payload.message}"
    return ChatResponse(reply=reply)
