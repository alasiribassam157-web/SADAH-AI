"""SADAH platform server.  Run:  py app.py   →  http://localhost:8000

On Vercel the same `app` is served without PyTorch: the brains run on NumPy, and the training and
developer tools (which need PyTorch and a writable disk) are left out."""
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent import home_feed
from agent.orchestrator import NexusAgent
from agent.stats import UsageStats
from agent.tools import SAFE_MODE
from cv import api as cv_api

try:  # training + developer tools: only where PyTorch is installed (the laptop, Docker)
    import dev_api
    from core import trainer
    from core.training_job import TrainingJob
except ImportError:
    dev_api = trainer = TrainingJob = None

ROOT = Path(__file__).resolve().parent
DEVTOOLS = ROOT / "devtools"  # developer dashboard: kept on the laptop only (gitignored)

app = FastAPI(title="SADAH", version="3.1")
app.mount("/ui", StaticFiles(directory=ROOT / "ui"), name="ui")
agent = NexusAgent()
stats = UsageStats()
job = TrainingJob(on_done=lambda name: agent.brains[name].reload()) if TrainingJob else None
if dev_api:
    app.include_router(dev_api.build_router(agent, stats, job))
app.include_router(cv_api.build_router())


class ChatIn(BaseModel):
    message: str
    session: str = ""  # per-tab id from the browser, used only for follow-up questions


@app.on_event("startup")
def _bootstrap():
    if job and not all(trainer.checkpoint(name).exists() for name in agent.brains):
        job.start()  # weights normally ship in models/; train only if they are missing


@app.get("/")
def index():
    # no-cache: browsers check for a new page after every deploy instead of mixing old HTML with new CSS
    return FileResponse(ROOT / "ui" / "index.html", headers={"Cache-Control": "no-cache"})


@app.get("/dev")
@app.get("/dev/{name}")
def dev_page(request: Request, name: str = "dev.html"):
    path = DEVTOOLS / Path(name).name
    if not dev_api or not dev_api.is_local(request) or not path.is_file():
        raise HTTPException(404)
    return FileResponse(path)


@app.get("/api/home")
def home_tiles(city: str = "الرياض", lang: str = "ar"):
    """Live dashboard tiles for the home page (cached 10 minutes per city)."""
    return home_feed.home(city.strip()[:40] or "الرياض", "en" if lang == "en" else "ar")


@app.get("/api/health")
def health():
    return {"status": "ok", "model_ready": all(b.ready for b in agent.brains.values())}


@app.post("/api/chat")
def chat(body: ChatIn, request: Request):
    message = body.message.strip()[:4000]
    if not message:
        raise HTTPException(400, "Empty message")
    # Real code/system execution only for the developer sitting at this machine.
    allow_exec = not SAFE_MODE and dev_api is not None and dev_api.is_local(request)
    result = agent.handle(message, allow_exec=allow_exec, session=body.session[:64])
    stats.record(message, result)
    return result


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    # ASCII only: Windows consoles without UTF-8 cannot print arrows and would crash the server.
    print(f"\n  SADAH ->  http://localhost:{port}    developer: http://localhost:{port}/dev\n")
    uvicorn.run(app, host=host, port=port, log_level="warning")
