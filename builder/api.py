"""Builder endpoints.

POST /api/build      {request}  -> {ok, message, question, problems, kind, name, files, preview}
POST /api/build/edit {spec, instruction} -> the same shape plus {note, changed}; the spec is the one /api/build returned
POST /api/build/zip  {request} or {spec} -> the project as a .zip (400 when it cannot be built)

`respond` has no web dependency, so it is tested without FastAPI. `preview` is one self-contained page
(css and app.js inlined) for a sandboxed iframe in the UI; the zip always holds the separate files.
"""
from builder import edit, specio
from builder.build import Result, build, render, to_zip

MAX_REQUEST = 1000


def preview(files: dict[str, str]) -> str:
    html = files["index.html"]
    html = html.replace('<link rel="stylesheet" href="style.css">', f"<style>{files['style.css']}</style>")
    if "app.js" in files:
        html = html.replace('<script src="app.js"></script>', f"<script>{files['app.js']}</script>")
    return html


def _answer(r: Result) -> dict:
    out = {"ok": r.ok, "message": r.message, "question": r.question, "problems": r.problems,
           "kind": r.spec.kind if r.spec else "", "name": r.spec.name if r.spec else "",
           "files": {}, "preview": "", "spec": None}
    if r.ok:
        out.update(files=r.files, preview=preview(r.files), spec=specio.to_dict(r.spec))
    return out


def respond(request: str) -> dict:
    return _answer(build(request.strip()[:MAX_REQUEST]))


def respond_edit(spec_data, instruction: str) -> dict:
    """One edit step. The spec comes from the browser, so it is validated before anything else."""
    spec, bad = specio.check(spec_data)
    if bad:
        return _answer(Result(False, problems=bad))
    done = edit.apply(spec, instruction[:MAX_REQUEST])
    out = _answer(render(done.spec))
    return {**out, "note": done.note, "changed": done.changed}


def zip_of(request: str = "", spec_data=None) -> bytes | None:
    """The project as a zip, from a request or from an (edited) spec; None when it cannot be built."""
    if spec_data is not None:
        spec, bad = specio.check(spec_data)
        r = render(spec) if spec and not bad else None
    else:
        r = build(request.strip()[:MAX_REQUEST])
    return to_zip(r.files) if r and r.ok else None


def build_router():
    from fastapi import APIRouter, HTTPException
    from fastapi.responses import Response
    from pydantic import BaseModel

    class BuildIn(BaseModel):
        request: str

    class EditIn(BaseModel):
        spec: dict
        instruction: str

    class ZipIn(BaseModel):
        request: str = ""
        spec: dict | None = None

    router = APIRouter()

    @router.post("/api/build")
    def build_site(body: BuildIn):
        if not body.request.strip():
            raise HTTPException(400, "Empty request")
        return respond(body.request)

    @router.post("/api/build/edit")
    def edit_site(body: EditIn):
        if not body.instruction.strip():
            raise HTTPException(400, "Empty instruction")
        return respond_edit(body.spec, body.instruction)

    @router.post("/api/build/zip")
    def build_zip(body: ZipIn):
        data = zip_of(body.request, body.spec)
        if data is None:
            raise HTTPException(400, "cannot build")
        return Response(data, media_type="application/zip",
                        headers={"Content-Disposition": 'attachment; filename="project.zip"'})

    return router
