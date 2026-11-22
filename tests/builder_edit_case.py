"""Checks one edit case: (project request, instruction, expectations) -> list of what went wrong."""
from builder.build import build, render
from builder.edit import apply
from builder.norm import n


def check(request: str, instruction: str, exp: dict) -> list[str]:
    spec = build(request).spec
    e = apply(spec, instruction)
    out = []
    if e.changed != exp["changed"]:
        out.append(f"changed={e.changed}")
    if "note_has" in exp and exp["note_has"] not in e.note:
        out.append(f"note={e.note}")
    s = e.spec
    for key, val in (("accent", s.accent), ("name", s.name)):
        if key in exp and exp[key] != val:
            out.append(f"{key}={val}")
    for key in ("phone", "email", "hours", "date", "time", "place", "city"):
        if key in exp and s.facts.get(key) != exp[key]:
            out.append(f"{key}={s.facts.get(key)}")
    out += [f"missing section {x}" for x in exp.get("sections_has", []) if x not in s.sections]
    out += [f"kept section {x}" for x in exp.get("sections_not", []) if x in s.sections]
    out += [f"missing service {x}" for x in exp.get("services_has", []) if x not in s.services]
    out += [f"missing item {x}" for x in exp.get("items_has", []) if tuple(x) not in s.items]
    out += [f"kept item {x}" for x in exp.get("items_not", []) if any(n(x) == n(i[0]) for i in s.items)]
    out += [f"missing point {x}" for x in exp.get("data_has", []) if tuple(x) not in s.data]
    if e.changed and not render(s).ok:
        out.append("the edited spec does not build")
    return out
