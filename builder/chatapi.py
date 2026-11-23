"""POST /api/chat {messages:[{role,content}], spec?} -> {reply, suggestions, engine, build}; GET /api/chat/status -> {engine}.
`engine` is "model" only when the owner turned a model on and this turn used it; otherwise "rules". `build` has the same shape as /api/build's answer."""
from builder import api, chat, llm


def respond(messages, spec_data=None, visitor: str = "") -> dict:
    ok = not llm.enabled() or llm.allow(visitor or "?")
    got = chat.turn(messages, spec_data, use_model=ok)
    out = {"reply": got.reply, "suggestions": got.suggestions[:4], "engine": got.engine, "build": api._answer(got.result) if got.result else None}
    if not ok:
        out["reply"] += "\n(وصلت للحد الأعلى للمحادثة الذكية هذه الساعة، فأجبتك بالقواعد.)"
    return out


def build_router():
    from fastapi import APIRouter, Request
    from pydantic import BaseModel

    class ChatIn(BaseModel):
        messages: list[dict]
        spec: dict | None = None

    router = APIRouter()

    @router.get("/api/chat/status")
    def status():
        return {"engine": "model" if llm.enabled() else "rules"}

    @router.post("/api/chat")
    def talk(body: ChatIn, request: Request):
        fwd = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        return respond(body.messages, body.spec, fwd or (request.client.host if request.client else ""))

    return router
