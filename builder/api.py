"""Builder endpoints.

POST /api/build      {request}  -> {ok, message, question, problems, kind, name, files, preview}
POST /api/build/zip  {request}  -> the project as a .zip (400 when the request cannot be built)

`respond` has no web dependency, so it is tested without FastAPI. `preview` is one self-contained page
(css and app.js inlined) for a sandboxed iframe in the UI; the zip always holds the separate files.
"""
from builder.build import build, to_zip

MAX_REQUEST = 1000


def preview(files: dict[str, str]) -> str:
    html = files["index.html"]
    html = html.replace('<link rel="stylesheet" href="style.css">', f"<style>{files['style.css']}</style>")
    if "app.js" in files:
        html = html.replace('<script src="app.js"></script>', f"<script>{files['app.js']}</script>")
    return html


def respond(request: str) -> dict:
    r = build(request.strip()[:MAX_REQUEST])
    out = {"ok": r.ok, "message": r.message, "question": r.question, "problems": r.problems,
           "kind": r.spec.kind if r.spec else "", "name": r.spec.name if r.spec else "",
           "files": {}, "preview": ""}
    if r.ok:
        out["files"] = r.files
        out["preview"] = preview(r.files)
    return out


def build_router():
    from fastapi import APIRouter, HTTPException
    from fastapi.responses import Response
    from pydantic import BaseModel

    class BuildIn(BaseModel):
        request: str

    router = APIRouter()

    @router.post("/api/build")
    def build_site(body: BuildIn):
        if not body.request.strip():
            raise HTTPException(400, "Empty request")
        return respond(body.request)

    @router.post("/api/build/zip")
    def build_zip(body: BuildIn):
        r = build(body.request.strip()[:MAX_REQUEST])
        if not r.ok:
            raise HTTPException(400, r.question or r.message or "cannot build")
        return Response(to_zip(r.files), media_type="application/zip",
                        headers={"Content-Disposition": 'attachment; filename="project.zip"'})

    return router
