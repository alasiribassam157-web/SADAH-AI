"""Spec <-> JSON. The edit endpoint is stateless: the browser sends the spec back with each instruction, so it is
untrusted input and is rebuilt field by field with strict types and size caps (never `Spec(**data)`)."""
import re
from dataclasses import asdict

from builder.spec import Spec, problems

MAX_ITEMS, MAX_TEXT = 40, 120
_FACT_KEYS = ("phone", "email", "city", "hours", "date", "time", "place")


def to_dict(spec: Spec) -> dict:
    return asdict(spec)


def _text(v, cap=MAX_TEXT) -> str:
    if not isinstance(v, str) or len(v) > cap:
        raise ValueError("bad text")
    return v


def _pairs(rows, value) -> list:
    if not isinstance(rows, list) or len(rows) > MAX_ITEMS:
        raise ValueError("bad list")
    out = []
    for row in rows:
        if not (isinstance(row, (list, tuple)) and len(row) == 2):
            raise ValueError("bad pair")
        out.append((_text(row[0]), value(row[1])))
    return out


def _number(v) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)) or abs(v) > 1e12:
        raise ValueError("bad number")
    return float(v)


def from_dict(d) -> Spec:
    """Validated Spec, or ValueError. Buildability (kind, name, sections, accent) is spec.problems' job."""
    if not isinstance(d, dict):
        raise ValueError("bad spec")
    facts = d.get("facts", {})
    services = d.get("services", [])
    sections = d.get("sections", [])
    if not (isinstance(facts, dict) and isinstance(services, list) and isinstance(sections, list)
            and len(services) <= MAX_ITEMS and len(sections) <= 10):
        raise ValueError("bad spec")
    spec = Spec(kind=_text(d.get("kind", "")), name=_text(d.get("name", "")), business=_text(d.get("business", "")),
                sections=[_text(s, 30) for s in sections], accent=_text(d.get("accent", ""), 7), lang="ar",
                data=_pairs(d.get("data", []), _number), items=_pairs(d.get("items", []), lambda v: _text(v, 40)),
                app=_text(d.get("app", ""), 20), game=_text(d.get("game", "memory"), 20),
                facts={k: _text(v, 80) for k, v in facts.items() if k in _FACT_KEYS},
                services=[_text(s, 80) for s in services])
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", spec.accent):   # it is written into the CSS: hex only
        raise ValueError("bad colour")
    return spec


def check(d) -> tuple[Spec | None, list[str]]:
    try:
        spec = from_dict(d)
    except ValueError:
        return None, ["بيانات المشروع غير صالحة"]
    return spec, problems(spec)
