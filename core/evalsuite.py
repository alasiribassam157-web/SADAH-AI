"""Deterministic, offline regression suites for the brains: per-skill accuracy of a given weights file.

No network, no agents, no critic: only the brain itself is measured, on questions it never trains on.
    router: "heldout" (tests/heldout_cases.py) + "benchmark" (the 310 official questions, expected intent only)
    coder : "coder_heldout" (tests/coder_heldout.py)
    both  : every tests/eval_extra/<brain>/*.jsonl file is one more suite (how a new skill brings its tests)
Runs on PyTorch when installed, otherwise on the NumPy backend (same predictions, see tests/numpy_parity.py).
"""
import json
import re
from pathlib import Path

from core.inference import BrainInference

EXTRA = Path(__file__).resolve().parent.parent / "tests" / "eval_extra"
_PUNCT = re.compile(r"[\s؟?!.،,:؛]+")


def normalize(text: str) -> str:
    """Comparison form of a question: lower-case, no punctuation, single spaces."""
    return _PUNCT.sub(" ", text.casefold()).strip()


def _extra(brain: str) -> dict[str, list[tuple[str, str]]]:
    suites = {}
    for path in sorted((EXTRA / brain).glob("*.jsonl")):
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        suites[path.stem] = [(r["q"], r["intent"]) for r in rows]
    return suites


def load_suites(brain: str) -> dict[str, list[tuple[str, str]]]:
    """suite name -> [(question, expected label)]"""
    if brain == "router":
        from tests.benchmark_cases import CASES_V3
        from tests.benchmark_cases_v4 import CASES_V4
        from tests.benchmark_cases_v5 import CASES_V5
        from tests.benchmark_cases_v6 import CASES_V6
        from tests.heldout_cases import HELDOUT
        suites = {"heldout": [(q, intent) for intent, qs in HELDOUT.items() for q in qs],
                  "benchmark": [(c[0], c[1]) for c in CASES_V3 + CASES_V4 + CASES_V5 + CASES_V6]}
    elif brain == "coder":
        from tests.coder_heldout import CODER_HELDOUT
        suites = {"coder_heldout": [(q, task) for task, qs in CODER_HELDOUT.items() for q in qs]}
    else:
        raise ValueError(f"unknown brain: {brain}")
    return {**suites, **_extra(brain)}


def held_out_questions() -> set[str]:
    """Every evaluation question (normalised): the training pipeline must never learn from these."""
    out: set[str] = set()
    for brain in ("router", "coder"):
        out |= {normalize(q) for suite in load_suites(brain).values() for q, _ in suite}
    return out


def _bucket(report: dict, skill: str) -> dict:
    return report["by_skill"].setdefault(skill, {"correct": 0, "total": 0})


def evaluate(brain: str, weights: Path, suites: dict | None = None) -> dict:
    """Run every suite through the brain stored in `weights`. Report shape (stable, saved in meta.json):
    {"labels": [...], "suites": {name: {"total", "correct", "by_skill": {skill: {"correct", "total"}},
    "cases": [{"q", "want", "got", "ok"}]}}}"""
    model = BrainInference(brain, path=weights)
    if not model.ready:
        raise FileNotFoundError(f"cannot load {weights}")
    report: dict = {"labels": list(model.intents), "suites": {}}
    for name, cases in (suites or load_suites(brain)).items():
        out = {"total": 0, "correct": 0, "by_skill": {}, "cases": []}
        for question, want in cases:
            got = model.predict(question)[0]
            ok = got == want
            out["total"] += 1
            out["correct"] += ok
            bucket = _bucket(out, want)
            bucket["total"] += 1
            bucket["correct"] += ok
            out["cases"].append({"q": question, "want": want, "got": got, "ok": ok})
        report["suites"][name] = out
    return report
