"""Scores the builder on the Arabic request suite: correct / total overall and per kind (landing, game, ask, refuse …)."""
from builder import checks
from builder.build import build as default_build
from tests.builder_requests import SKILLS, SUITE


def _matches(spec, expect: dict) -> bool:
    for key, want in expect.items():
        if key == "sections":
            ok = all(s in spec.sections for s in want)
        elif key == "data_labels":
            ok = [label for label, _ in spec.data] == want
        elif key == "items_n":
            ok = len(spec.items) == want
        elif key == "services":
            ok = list(spec.services) == want
        elif key in ("phone", "email", "city", "hours", "date", "time", "place"):
            ok = spec.facts.get(key) == want
        else:
            ok = getattr(spec, key) == want
        if not ok:
            return False
    return True


def judge(case: dict, r) -> bool:
    skill = case["skill"]
    if skill == "ask":
        return not r.ok and bool(r.question) and not r.files
    if skill == "refuse":
        return not r.ok and bool(r.message) and not r.files
    return bool(r.ok and r.spec.kind == skill and not checks.check_site(r.files) and _matches(r.spec, case["expect"]))


def evaluate(build=default_build, suite=None) -> dict:
    out = {"total": 0, "correct": 0, "by_skill": {s: {"correct": 0, "total": 0} for s in SKILLS}, "cases": []}
    for case in suite if suite is not None else SUITE:
        ok = judge(case, build(case["q"]))
        out["total"] += 1
        out["correct"] += ok
        bucket = out["by_skill"][case["skill"]]
        bucket["total"] += 1
        bucket["correct"] += ok
        out["cases"].append({"q": case["q"], "want": case["skill"], "got": "ok" if ok else "fail", "ok": ok})
    return {"labels": list(SKILLS), "suites": {"builder_requests": out}}
