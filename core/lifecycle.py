"""Brain lifecycle: init, status, evaluate, review (gate), promote, reject, rollback, new-experiment.

    python -m core.lifecycle init                     register the weights in models/ as the first stable version
    python -m core.lifecycle status
    python -m core.lifecycle evaluate router [--version N]
    python -m core.lifecycle review router 3          run the gate on candidate v3 (exit code 1 = rejected)
    python -m core.lifecycle promote router 3         make a gate-approved candidate the served brain
    python -m core.lifecycle reject router 3 --reason "why"
    python -m core.lifecycle rollback router [--to N]
    python -m core.lifecycle new-experiment add-skill-x --brain router --size pretrained --epochs 12
Nothing here needs PyTorch (evaluation falls back to NumPy); only training does.
"""
import time

from core import evalsuite, gate
from core.inference import BrainInference
from core.registry import PASSED, REJECTED, Registry, RegistryError

BRAINS = ("router", "coder")


def summary(report: dict) -> dict:
    """The report without per-question cases (small enough to commit in meta.json)."""
    return {"labels": report["labels"], "suites": {n: {k: v for k, v in s.items() if k != "cases"}
                                                   for n, s in report["suites"].items()}}


def init(brain: str, reg: Registry, evaluator=evalsuite.evaluate) -> int:
    """Register the weights already in models/ as the baseline. Does nothing if a stable version exists."""
    if reg.stable(brain) is not None:
        return reg.stable(brain)
    served = reg.served(brain)
    info = BrainInference(brain, path=served).info
    version = reg.add(brain, served, {k: v for k, v in info.items() if k != "backend"}, status=PASSED)
    reg.update(brain, version, eval=summary(evaluator(brain, served)), note="baseline imported by `init`")
    reg.promote(brain, version, via="init")
    return version


def review(brain: str, version: int, reg: Registry, evaluator=evalsuite.evaluate) -> dict:
    """Judge candidate `version` against the stable brain. Rejected candidates are marked and can never be promoted."""
    stable = reg.stable(brain)
    if stable is None:
        raise RegistryError(f"{brain} has no stable version yet: run `python -m core.lifecycle init`")
    if version == stable:
        raise RegistryError(f"{brain} v{version} is already the stable version")
    if not reg.served_matches_stable(brain):
        raise RegistryError(f"models/{brain}.pt does not match the registered stable v{stable}: fix that first")
    base, cand = evaluator(brain, reg.served(brain)), evaluator(brain, reg.weights(brain, version))
    verdict = gate.compare(base, cand, gate.load_config(reg.models))
    reg.update(brain, version, eval=summary(cand), gated_against=stable, reviewed=time.strftime("%Y-%m-%d %H:%M"),
               gate={k: verdict[k] for k in ("passed", "reasons", "overall", "regressions", "fixes")},
               status=PASSED if verdict["passed"] else REJECTED,
               **({} if verdict["passed"] else {"reason": "; ".join(verdict["reasons"])[:500]}))
    reg.log(brain, "review", version, passed=verdict["passed"], against=stable)
    return verdict


def promote(brain: str, version: int, reg: Registry) -> None:
    meta = reg.meta(brain, version)
    if meta.get("gated_against") != reg.stable(brain):
        raise RegistryError(f"{brain} v{version} was reviewed against v{meta.get('gated_against')} but the stable "
                            f"version is now v{reg.stable(brain)}: run `review` again")
    reg.promote(brain, version)


def review_and_promote(brain: str, version: int, reg: Registry | None = None) -> dict:
    """What the dashboard's training job calls: promote only when the gate passes. Returns the verdict."""
    reg = reg or Registry()
    if reg.stable(brain) is None:
        if reg.served(brain).exists():
            init(brain, reg)   # the weights already in models/ become the baseline the candidate is judged against
        else:   # the very first brain: nothing to regress from
            reg.update(brain, version, status=PASSED, gated_against=None, note="first version, no baseline to compare")
            reg.promote(brain, version)
            return {"passed": True, "reasons": [], "overall": {}, "regressions": [], "fixes": [], "rows": []}
    verdict = review(brain, version, reg)
    if verdict["passed"]:
        promote(brain, version, reg)
    return verdict


if __name__ == "__main__":
    import sys

    from core.lifecycle_cli import main
    sys.exit(main())
