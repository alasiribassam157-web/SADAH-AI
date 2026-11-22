"""The regression gate: decides whether a candidate brain may replace the stable one.

Both reports come from core.evalsuite on the same questions. A candidate is rejected when:
  * it lost a label the stable brain had (a skill disappeared),
  * overall accuracy on the skills the stable brain knows drops by more than `max_overall_drop`, in any suite,
  * any single skill drops by more than `max_skill_drop` (override per skill in `skill_overrides`),
  * a brand-new skill is below `min_new_skill_accuracy`.
Limits are absolute accuracy fractions (0.05 = five points) and live in models/gate.json, so changing them is
a visible, reviewable commit. Pure functions: no files, no PyTorch.
"""
import json
from pathlib import Path

DEFAULTS = {"max_overall_drop": 0.01, "max_skill_drop": 0.05, "min_new_skill_accuracy": 0.80, "skill_overrides": {}}
EPS = 1e-9


def load_config(models_dir: Path) -> dict:
    path = Path(models_dir) / "gate.json"
    return {**DEFAULTS, **(json.loads(path.read_text(encoding="utf-8")) if path.exists() else {})}


def _acc(cell: dict) -> float:
    return cell["correct"] / cell["total"] if cell["total"] else 1.0


def _sum(cells: list[dict]) -> dict:
    return {"correct": sum(c["correct"] for c in cells), "total": sum(c["total"] for c in cells)}


def compare(baseline: dict, candidate: dict, config: dict | None = None) -> dict:
    cfg = {**DEFAULTS, **(config or {})}
    known, reasons, rows, regressions, fixes, overall = set(baseline["labels"]), [], [], [], [], {}
    for label in sorted(known - set(candidate["labels"])):
        reasons.append(f"skill '{label}' exists in the stable brain but not in the candidate")
    for name, base in baseline["suites"].items():
        cand = candidate["suites"].get(name)
        if cand is None:
            reasons.append(f"suite '{name}' is missing from the candidate report")
            continue
        for skill in sorted(set(base["by_skill"]) | set(cand["by_skill"])):
            b = base["by_skill"].get(skill, {"correct": 0, "total": 0})
            c = cand["by_skill"].get(skill, {"correct": 0, "total": 0})
            if not c["total"]:
                continue
            row = {"suite": name, "skill": skill, "before": b, "after": c, "new": skill not in known, "ok": True}
            if skill in known:
                row["drop"] = round(_acc(b) - _acc(c), 4)
                limit = cfg["skill_overrides"].get(skill, cfg["max_skill_drop"])
                if row["drop"] > limit + EPS:
                    row["ok"] = False
                    reasons.append(f"[{name}] {skill}: {b['correct']}/{b['total']} -> {c['correct']}/{c['total']} "
                                   f"(drop {row['drop']:.1%} > allowed {limit:.1%})")
            elif _acc(c) + EPS < cfg["min_new_skill_accuracy"]:
                row["ok"] = False
                reasons.append(f"[{name}] new skill {skill}: {_acc(c):.1%} < required {cfg['min_new_skill_accuracy']:.1%}")
            rows.append(row)
        old_b = _sum([v for k, v in base["by_skill"].items() if k in known])
        old_c = _sum([v for k, v in cand["by_skill"].items() if k in known])
        overall[name] = {"before": old_b, "after": old_c}
        if old_b["total"] and _acc(old_b) - _acc(old_c) > cfg["max_overall_drop"] + EPS:
            reasons.append(f"[{name}] overall on known skills: {_acc(old_b):.1%} -> {_acc(old_c):.1%} "
                           f"(allowed drop {cfg['max_overall_drop']:.1%})")
        before = {x["q"]: x for x in base["cases"]}
        for case in cand["cases"]:
            old = before.get(case["q"])
            if old and old["ok"] and not case["ok"]:
                regressions.append({"suite": name, "q": case["q"], "want": case["want"], "got": case["got"]})
            elif old and not old["ok"] and case["ok"]:
                fixes.append({"suite": name, "q": case["q"], "want": case["want"]})
    return {"passed": not reasons, "reasons": reasons, "rows": rows, "overall": overall,
            "regressions": regressions, "fixes": fixes, "config": cfg}


def render(verdict: dict) -> str:
    """Human-readable table: per suite and skill, before -> after."""
    lines = []
    for name, o in verdict["overall"].items():
        lines.append(f"[{name}] overall (known skills): {o['before']['correct']}/{o['before']['total']} -> "
                     f"{o['after']['correct']}/{o['after']['total']}")
    for r in verdict["rows"]:
        b, a = r["before"], r["after"]
        before = f"{b['correct']}/{b['total']}" if b["total"] else "  new "
        lines.append(f"  {'OK  ' if r['ok'] else 'FAIL'} [{r['suite']}] {r['skill']:<16} {before:>7} -> {a['correct']}/{a['total']}")
    lines += [f"  regression: '{x['q']}' want={x['want']} now={x['got']}" for x in verdict["regressions"]]
    lines += [f"  fixed: '{x['q']}'" for x in verdict["fixes"]]
    lines.append("GATE: PASS" if verdict["passed"] else "GATE: REJECT")
    lines += [f"  - {why}" for why in verdict["reasons"]]
    return "\n".join(lines)
