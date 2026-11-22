"""Deterministic evaluation of a text generator (the future generative brain) with the same report shape as
core.evalsuite, so core.gate can compare a generative candidate against the stable one.

A generator is any callable  generate(question: str, context: list[str]) -> str.
Built from SADAH's own country facts (data/kb/facts_cache.json); nothing here calls a model.
  skills capital / currency / language : answer must contain the fact when the context states it (grounded)
  skill  abstain                       : invented entities, no context -> the generator must say it does not know
  skill  supported                     : grounded answers must not add content words absent from the context
"""
import json
import re
from pathlib import Path

FACTS = Path(__file__).resolve().parent.parent / "data" / "kb" / "facts_cache.json"
ABSTAIN = ("لا أعرف", "لا اعرف", "لا أملك", "لا توجد معلومات", "لا أستطيع التأكد", "ما عندي معلومة")
INVENTED = ["زوراء", "كارفستان", "بيلوريا", "أنداريا الشمالية", "ماركستان", "ثالاسيا", "دولة نورفيل", "سيلفانيا"]
FIELDS = {"capital": ("P36", "ما عاصمة {}؟", "عاصمة {} هي {}."),
          "currency": ("P38", "ما عملة {}؟", "عملة {} هي {}."),
          "language": ("P37", "ما لغة {} الرسمية؟", "اللغة الرسمية في {} هي {}.")}
SKILLS = [*FIELDS, "abstain", "supported"]
_WORD = re.compile(r"\w+", re.UNICODE)
_STOP = {"في", "من", "هي", "هو", "على", "إلى", "عن", "ما", "و", "ال", "هذا", "هذه", "أن", "إن", "كان", "التي", "الذي"}


def _is_arabic(text: str) -> bool:
    return bool(text) and all("؀" <= c <= "ۿ" or c.isspace() for c in text)


def build_suite(path: Path = FACTS) -> list[dict]:
    """[{skill, q, context, want}] where want is the fact to contain, or None for an abstention case."""
    countries = dict(json.loads(path.read_text(encoding="utf-8")))["countries"]
    cases = []
    for c in sorted(countries, key=lambda c: c["ar"]):
        for skill, (prop, question, sentence) in FIELDS.items():
            value = next((v for v in c.get(prop, []) if _is_arabic(v)), None)
            if value:
                cases.append({"skill": skill, "q": question.format(c["ar"]),
                              "context": [sentence.format(c["ar"], value)], "want": value})
    for name in INVENTED:
        cases.append({"skill": "abstain", "q": f"ما عاصمة {name}؟", "context": [], "want": None})
    return cases


def abstains(answer: str) -> bool:
    return any(m in answer for m in ABSTAIN)


def unsupported_share(answer: str, context: list[str]) -> float:
    """Share of the answer's content words that appear nowhere in the context (heuristic hallucination signal)."""
    known = {w for t in context for w in _WORD.findall(t)}
    words = [w for w in _WORD.findall(answer) if w not in _STOP and len(w) > 2]
    return sum(w not in known for w in words) / len(words) if words else 0.0


def evaluate(generate, suite: list[dict] | None = None, max_unsupported: float = 0.2) -> dict:
    """Run `generate` over the suite -> core.evalsuite report shape ({"labels", "suites": {"gen_facts": ...}})."""
    out = {"total": 0, "correct": 0, "by_skill": {s: {"correct": 0, "total": 0} for s in SKILLS}, "cases": []}

    def add(skill: str, q: str, want, got, ok: bool):
        out["total"] += 1
        out["correct"] += ok
        out["by_skill"][skill]["total"] += 1
        out["by_skill"][skill]["correct"] += ok
        out["cases"].append({"q": q, "want": want, "got": got, "ok": ok})

    for case in suite if suite is not None else build_suite():
        answer = generate(case["q"], case["context"])
        if case["want"] is None:
            add("abstain", case["q"], "abstain", answer, abstains(answer))
            continue
        add(case["skill"], case["q"], case["want"], answer, case["want"] in answer and not abstains(answer))
        share = unsupported_share(answer, case["context"])
        add("supported", case["q"], f"<= {max_unsupported:.0%} unsupported", answer, share <= max_unsupported)
    return {"labels": list(SKILLS), "suites": {"gen_facts": out}}
