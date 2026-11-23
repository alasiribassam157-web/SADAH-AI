"""POST /api/chat {messages:[{role,content}], spec?} -> {reply, suggestions, build}; `build` has the same shape as /api/build's answer (or null)."""
from builder import api, chat


def respond(messages, spec_data=None) -> dict:
    got = chat.turn(messages, spec_data)
    return {"reply": got.reply, "suggestions": got.suggestions[:4], "build": api._answer(got.result) if got.result else None}


def build_router():
    from fastapi import APIRouter
    from pydantic import BaseModel

    class ChatIn(BaseModel):
        messages: list[dict]
        spec: dict | None = None

    router = APIRouter()

    @router.post("/api/chat")
    def talk(body: ChatIn):
        return respond(body.messages, body.spec)

    return router
