"""Publish to a link without any hosting account or storage: the link carries the project itself.

/s/<token>/ holds the compressed spec (JSON -> zlib -> base64url); opening it validates the spec like any edit does and builds the site
on the spot, so nothing is stored and nothing can go stale. The token is read as untrusted input (size caps, no zip bombs), pages are
served with a strict Content-Security-Policy, and every shared page says in its footer that it was made with sadah, so a link cannot pass
for someone's official site. Limits: it works while sadah is up, and a later change to a template changes how old links look."""
import base64
import json
import zlib

from builder import specio
from builder.build import render

MAX_TOKEN, MAX_JSON = 6000, 60_000
FILES = {"index.html": "text/html; charset=utf-8", "style.css": "text/css; charset=utf-8", "app.js": "text/javascript; charset=utf-8"}
HEADERS = {"Content-Security-Policy": "default-src 'none'; style-src 'self'; script-src 'self'; img-src data:; base-uri 'none'; form-action 'none'; frame-ancestors 'self'",
           "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer", "Cache-Control": "public, max-age=300"}


def encode(spec_data: dict) -> str | None:
    """The token for a spec the browser sent, or None when the spec is invalid or the link would be too long."""
    spec, bad = specio.check(spec_data)
    if bad or spec is None:
        return None
    raw = zlib.compress(json.dumps(specio.to_dict(spec), ensure_ascii=False, separators=(",", ":")).encode("utf-8"), 9)
    token = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    return token if len(token) <= MAX_TOKEN else None


def files_of(token: str) -> dict[str, str] | None:
    """The site a token stands for, or None for anything that is not a valid, buildable project."""
    if not token or len(token) > MAX_TOKEN:
        return None
    try:
        raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
        box = zlib.decompressobj()
        data = box.decompress(raw, MAX_JSON)
        if box.unconsumed_tail:   # bigger than the cap: a zip bomb or not ours
            return None
        spec, bad = specio.check(json.loads(data.decode("utf-8")))
    except (ValueError, zlib.error, UnicodeDecodeError):
        return None
    if bad or spec is None:
        return None
    r = render(spec)
    if not r.ok:
        return None
    files = dict(r.files)
    files["index.html"] = files["index.html"].replace("</footer>", ' · صُنع بأداة <a href="/">sadah</a></footer>', 1)
    return files


def build_router():
    from fastapi import APIRouter, HTTPException
    from fastapi.responses import RedirectResponse, Response
    from pydantic import BaseModel

    class ShareIn(BaseModel):
        spec: dict

    router = APIRouter()

    @router.post("/api/share")
    def share(body: ShareIn):
        token = encode(body.spec)
        if token is None:
            raise HTTPException(400, "cannot share")
        return {"url": f"/s/{token}/"}

    @router.get("/s/{token}")
    def bare(token: str):
        return RedirectResponse(f"/s/{token}/")

    @router.get("/s/{token}/")
    @router.get("/s/{token}/{name}")
    def page(token: str, name: str = "index.html"):
        files = files_of(token)
        if files is None or name not in files:
            raise HTTPException(404, "not found")
        return Response(files[name], media_type=FILES[name].split(";")[0], headers={**HEADERS, "Content-Type": FILES[name]})

    return router
