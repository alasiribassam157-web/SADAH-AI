"""Developer-only API. Reachable only from the developer's own machine.

Anyone else (the public cloud link, the tunnel) gets 404, as if it did not exist.
The laptop can also read the cloud's stats through /api/dev/cloud using a private key
kept in .sadah_cloud.json (gitignored); the same key is set on Render as SADAH_ACCESS_TOKEN.
"""
import json
import os
import secrets
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from agent.tools import WORKSPACE
from core import finetune, trainer
from core.dataset_builder import BRAINS, INTENTS, add_custom, load_auto_labels, load_custom
from core.pretrain import LOG as PRETRAIN_LOG

ROOT = Path(__file__).resolve().parent
CLOUD_KEY = os.getenv("SADAH_ACCESS_TOKEN", "").strip()
CLOUD_CFG = ROOT / ".sadah_cloud.json"
# Every question people asked online, kept on the laptop (gitignored: the repo is public, questions are private).
ARCHIVE = ROOT / "data" / "cloud_questions.jsonl"
# Tunnels and cloud proxies add these; a request carrying any of them is not from this machine.
_PROXY_HEADERS = ("x-forwarded-for", "cf-connecting-ip", "x-real-ip", "forwarded")


def is_local(request: Request) -> bool:
    host = request.client.host if request.client else ""
    return host in ("127.0.0.1", "::1") and not any(h in request.headers for h in _PROXY_HEADERS)


def require_dev(request: Request):
    key = request.headers.get("x-sadah-key", "").strip()
    if is_local(request) or (CLOUD_KEY and key and secrets.compare_digest(key, CLOUD_KEY)):
        return
    raise HTTPException(status_code=404)


class TrainIn(BaseModel):
    brain: str = "all"
    size: str = "medium"
    epochs: int = 12


class TeachIn(BaseModel):
    text: str
    intent: str
    brain: str = "router"


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _benchmark() -> dict:
    return _read_json(trainer.MODELS / "benchmark.json")


def _archive(recent: list[dict]) -> list[dict]:
    """Append unseen cloud questions to the local archive and return the newest 200 of it."""
    rows = []
    if ARCHIVE.exists():
        rows = [json.loads(line) for line in ARCHIVE.read_text(encoding="utf-8").splitlines() if line.strip()]
    seen = {(r.get("date", ""), r["time"], r["text"]) for r in rows}
    new = [r for r in reversed(recent) if (r.get("date", ""), r["time"], r["text"]) not in seen]
    if new:
        ARCHIVE.parent.mkdir(exist_ok=True)
        with ARCHIVE.open("a", encoding="utf-8") as f:
            f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in new)
    return list(reversed(rows + new))[:200]


def build_router(agent, stats, job) -> APIRouter:
    router = APIRouter(prefix="/api/dev", dependencies=[Depends(require_dev)])

    @router.get("/overview")
    def overview():
        brains = {name: b.info for name, b in agent.brains.items()}
        return {"brain": agent.brain.info, "brains": brains, "usage": stats.snapshot(),
                "total_params": sum(info.get("params", 0) for info in brains.values()),
                "target_params": trainer.TARGET_PARAMS, "benchmark": _benchmark(),
                "versions": trainer.load_versions(), "taught": sum(len(load_custom(n)) for n in BRAINS),
                "intents": INTENTS, "sizes": list(trainer.SIZES) + (["pretrained"] if finetune.available() else [])}

    @router.get("/learning")
    def learning():
        """SADAH v5 learning metrics: pre-training progress, honest held-out score, self-training size."""
        return {"pretrain": _read_json(PRETRAIN_LOG) or None, "heldout": _read_json(trainer.MODELS / "heldout.json") or None,
                "brain_alone": _benchmark().get("brain_alone"), "auto_labels": len(load_auto_labels()),
                "pretrained_ready": finetune.available()}

    @router.post("/train")
    def train(body: TrainIn):
        if body.size not in (*trainer.SIZES, "pretrained") or body.brain not in (*BRAINS, "all"):
            raise HTTPException(400, f"size must be one of {list(trainer.SIZES)}; brain router|coder|all")
        return {"started": job.start(body.brain, body.size, max(1, min(body.epochs, 60)))}

    @router.get("/train/status")
    def train_status():
        return job.state

    @router.post("/teach")
    def teach(body: TeachIn):
        if body.brain not in BRAINS or body.intent not in BRAINS[body.brain][0] or not body.text.strip():
            raise HTTPException(400, "unknown brain/label or empty text")
        return {"taught": add_custom(body.text, body.intent, body.brain)}

    @router.get("/files")
    def files():
        items = [{"name": str(p.relative_to(WORKSPACE)).replace("\\", "/"), "size": p.stat().st_size,
                  "mtime": p.stat().st_mtime} for p in WORKSPACE.rglob("*") if p.is_file()]
        return sorted(items, key=lambda f: -f["mtime"])[:200]

    @router.get("/cloud")
    def cloud(request: Request):
        """Laptop only: fetch the live cloud platform's overview with the private key."""
        if not is_local(request):
            raise HTTPException(404)
        try:
            cfg = json.loads(CLOUD_CFG.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"configured": False}
        try:
            res = httpx.get(cfg["url"].rstrip("/") + "/api/dev/overview",
                            headers={"x-sadah-key": cfg["key"]}, timeout=70)
            res.raise_for_status()
        except httpx.HTTPError as exc:
            return {"configured": True, "url": cfg["url"], "error": str(exc)}
        data = res.json()
        data["usage"]["recent"] = _archive(data["usage"].get("recent", []))  # survives Render restarts
        data["archived"] = sum(1 for _ in ARCHIVE.open(encoding="utf-8")) if ARCHIVE.exists() else 0
        return {"configured": True, "url": cfg["url"], **data}

    return router
