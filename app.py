"""sadah: builds websites, small apps and games from an Arabic request. Rules only, no outside model.

Run:  python app.py   ->   http://localhost:8000
On Vercel the same `app` is served as a function; there is no state and no database."""
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from builder import api as builder_api, share

ROOT = Path(__file__).resolve().parent
app = FastAPI(title="sadah", version="4.0")
app.mount("/ui", StaticFiles(directory=ROOT / "ui"), name="ui")
app.include_router(builder_api.build_router())
app.include_router(share.build_router())


@app.get("/")
def index():
    # no-cache: browsers check for a new page after every deploy instead of mixing old HTML with new CSS
    return FileResponse(ROOT / "ui" / "index.html", headers={"Cache-Control": "no-cache"})


@app.get("/builder")
def old_builder_link():
    return RedirectResponse("/")


@app.get("/api/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    print(f"\n  sadah ->  http://localhost:{port}\n")
    uvicorn.run(app, host=host, port=port, log_level="warning")
