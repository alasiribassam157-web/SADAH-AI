"""Honest held-out test: 91 freshly written questions the brain never trains on (no template phrasing).

Measures the router brain ALONE (no critic, no internet), so it shows how well the brain itself
understands new ways of asking.   Run:  py -m tests.heldout     (writes models/heldout.json)
"""
import json
import time
from collections import Counter

from core.inference import MODELS, BrainInference
from tests.heldout_cases import HELDOUT


def run(verbose: bool = True) -> dict:
    brain, hits, misses = BrainInference("router"), Counter(), []
    total = sum(len(qs) for qs in HELDOUT.values())
    for intent, questions in HELDOUT.items():
        for q in questions:
            got, conf, _ = brain.predict(q)
            if got == intent:
                hits[intent] += 1
            else:
                misses.append({"q": q, "want": intent, "got": got, "confidence": round(conf, 2)})
    correct = sum(hits.values())
    report = {"date": time.strftime("%Y-%m-%d %H:%M"), "total": total, "correct": correct,
              "accuracy": round(correct / total, 4), "brain": brain.info.get("size"), "params": brain.info.get("params"),
              "by_intent": {k: f"{hits[k]}/{len(v)}" for k, v in HELDOUT.items()}, "misses": misses}
    (MODELS / "heldout.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    if verbose:
        for m in misses:
            print(f"  ✗ {m['q']}  want={m['want']} got={m['got']} ({m['confidence']})")
        print(f"\nHeld-out (brain alone, unseen phrasing): {correct}/{total} = {correct / total:.1%}")
    return report


if __name__ == "__main__":
    run()
