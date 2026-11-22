"""Request -> site: understand, render, check. Never hands over a site that failed its own checks."""
import io
import zipfile
from dataclasses import dataclass, field

from builder import checks, dashboard, landing, pages, shop, webapp, spec as spec_mod
from builder.understand import understand

RENDERERS = {"landing": landing.render, "dashboard": dashboard.render, "shop": shop.render, "webapp": webapp.render,
             "portfolio": pages.portfolio, "blog": pages.blog, "event": pages.event}


@dataclass
class Result:
    ok: bool
    files: dict[str, str] = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)
    question: str = ""
    message: str = ""
    spec: spec_mod.Spec | None = None


def build(request: str) -> Result:
    u = understand(request)
    if u.unsupported:
        return Result(False, message=u.unsupported)
    if u.question:
        return Result(False, question=u.question, spec=u.spec)
    bad = spec_mod.problems(u.spec)
    if bad:
        return Result(False, problems=bad, spec=u.spec)
    files = RENDERERS[u.spec.kind](u.spec)
    found = checks.check_site(files)
    if found:
        return Result(False, problems=found, spec=u.spec)
    return Result(True, files=files, spec=u.spec)


def to_zip(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for path, text in sorted(files.items()):
            z.writestr(path, text.encode("utf-8"))
    return buf.getvalue()
