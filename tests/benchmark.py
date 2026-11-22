"""Official SADAH benchmark: 310 realistic questions with the expected skill and answer.

Run:  py -m tests.benchmark      (writes models/benchmark.json, shown in the developer dashboard)
Exit code 1 when the end-to-end accuracy or the router brain alone is below its floor, so a script or CI can stop.
Some questions need the internet (Wikipedia, Wikidata): a failure caused by "Web request failed" is a network
problem, not a regression. The deterministic, offline per-skill gate is core/lifecycle.py (see docs/OPERATIONS.md).
"""
import json
import os
import sys
import time

from agent.orchestrator import SadahAgent
from core.inference import MODELS

from tests.benchmark_cases import CASES_V3
from tests.benchmark_cases_v4 import CASES_V4
from tests.benchmark_cases_v5 import CASES_V5
from tests.benchmark_cases_v6 import CASES_V6

MIN_ACCURACY = float(os.getenv("SADAH_BENCH_MIN", "0.98"))             # whole system, critic included
MIN_BRAIN_ALONE = float(os.getenv("SADAH_BENCH_BRAIN_MIN", "0.90"))    # the router brain without the critic
# Run `py -m tests.benchmark v3` to score only the SADAH v3 questions.
CASES = CASES_V3 if "v3" in sys.argv[1:] else CASES_V3 + CASES_V4 + CASES_V5 + CASES_V6


def run(verbose: bool = True) -> dict:
    agent, failures, by_intent = SadahAgent(), [], {}
    start, brain_alone = time.time(), 0
    for question, intent, expect in CASES:
        r = agent.handle(question)
        brain_alone += r.get("neural_intent") == intent  # honest score: the brain without the critic's help
        ok = r.get("intent") == intent and expect.lower() in r["answer"].lower()
        bucket = by_intent.setdefault(intent, [0, 0])
        bucket[0] += ok
        bucket[1] += 1
        if not ok:
            failures.append({"q": question, "want": intent, "got": r.get("intent"), "answer": r["answer"][:160]})
        if verbose:
            print(f"{'PASS' if ok else 'FAIL'}  [{r.get('intent')}] {question}", flush=True)
    passed = len(CASES) - len(failures)
    report = {"date": time.strftime("%Y-%m-%d %H:%M"), "total": len(CASES), "passed": passed,
              "accuracy": round(passed / len(CASES), 4), "seconds": round(time.time() - start, 1),
              "brain_alone": round(brain_alone / len(CASES), 4),
              "by_intent": {k: {"passed": v[0], "total": v[1]} for k, v in by_intent.items()}, "failures": failures}
    (MODELS / "benchmark.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return report


if __name__ == "__main__":
    result = run()
    print(f"\nBenchmark: {result['passed']}/{result['total']} = {result['accuracy']:.1%}  ({result['seconds']}s)"
          f"  | brain alone (no critic): {result['brain_alone']:.1%}")
    for f in result["failures"]:
        print(f"  ✗ {f['q']}  want={f['want']} got={f['got']}  → {f['answer'][:90]!r}")
    sys.exit(0 if result["accuracy"] >= MIN_ACCURACY and result["brain_alone"] >= MIN_BRAIN_ALONE else 1)
