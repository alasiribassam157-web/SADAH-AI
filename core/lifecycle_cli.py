"""Command line of core.lifecycle (kept apart so each file stays short)."""
import argparse
import json
import sys
import time
from pathlib import Path

from core import evalsuite, gate
from core.inference import BrainInference
from core.lifecycle import BRAINS, init, promote, review
from core.registry import Registry, RegistryError


def _print_status(reg: Registry) -> None:
    for brain in BRAINS:
        print(f"== {brain}: stable = v{reg.stable(brain)}" + ("" if reg.served_matches_stable(brain) else "  (!) models/%s.pt differs from the registry" % brain))
        for m in reg.versions(brain):
            held = next(iter((m.get("eval") or {"suites": {}})["suites"].values()), None)
            acc = f"{held['correct']}/{held['total']}" if held else "-"
            print(f"   v{m['version']:<3} {m['status']:<11} {m['created']}  {acc:>8}  exp={m['train'].get('experiment', '-')}"
                  f"  {m.get('reason', '')[:60]}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m core.lifecycle", description="SADAH brain lifecycle: init, status, evaluate, review, promote, reject, rollback, new-experiment")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("init", "status"):
        sub.add_parser(name)
    for name in ("evaluate", "review", "promote", "reject", "rollback"):
        p = sub.add_parser(name)
        p.add_argument("brain", choices=BRAINS)
        if name in ("review", "promote", "reject"):
            p.add_argument("version", type=int)
    imp = sub.add_parser("import")   # weights from elsewhere (an old git version, another machine) as a candidate
    imp.add_argument("brain", choices=BRAINS)
    imp.add_argument("path")
    sub.choices["evaluate"].add_argument("--version", type=int)
    sub.choices["reject"].add_argument("--reason", required=True)
    sub.choices["rollback"].add_argument("--to", type=int)
    exp = sub.add_parser("new-experiment")
    exp.add_argument("name")
    exp.add_argument("--brain", choices=BRAINS, default="router")
    exp.add_argument("--size", default="pretrained")
    exp.add_argument("--epochs", type=int, default=12)
    exp.add_argument("--notes", default="")
    a, reg = ap.parse_args(argv), Registry()
    try:
        if a.cmd == "init":
            print({b: f"v{init(b, reg)}" for b in BRAINS})
        elif a.cmd == "status":
            _print_status(reg)
        elif a.cmd == "evaluate":
            path = reg.weights(a.brain, a.version) if a.version else reg.served(a.brain)
            for name, s in evalsuite.evaluate(a.brain, path)["suites"].items():
                print(f"[{name}] {s['correct']}/{s['total']}  " + "  ".join(
                    f"{k}={v['correct']}/{v['total']}" for k, v in sorted(s["by_skill"].items())))
        elif a.cmd == "import":
            info = BrainInference(a.brain, path=Path(a.path)).info
            version = reg.add(a.brain, Path(a.path), {k: v for k, v in info.items() if k != "backend"})
            print(f"{a.brain} v{version} stored as a candidate: now `review` and `promote` it")
        elif a.cmd == "review":
            verdict = review(a.brain, a.version, reg)
            print(gate.render(verdict))
            return 0 if verdict["passed"] else 1
        elif a.cmd == "promote":
            promote(a.brain, a.version, reg)
            print(f"{a.brain} v{a.version} is now stable (models/{a.brain}.pt updated)")
        elif a.cmd == "reject":
            reg.reject(a.brain, a.version, a.reason)
            print(f"{a.brain} v{a.version} rejected")
        elif a.cmd == "rollback":
            print(f"{a.brain}: rolled back to v{reg.rollback(a.brain, a.to)}")
        elif a.cmd == "new-experiment":
            reg.root.joinpath("experiments").mkdir(parents=True, exist_ok=True)
            path = reg.root / "experiments" / f"{a.name}.json"
            if path.exists():
                raise RegistryError(f"experiment '{a.name}' already exists")
            path.write_text(json.dumps({"name": a.name, "brain": a.brain, "size": a.size, "epochs": a.epochs,
                                        "notes": a.notes, "created": time.strftime("%Y-%m-%d %H:%M")},
                                       ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"experiment created: {path}\nnext: python -m core.trainer --experiment {a.name}")
    except (RegistryError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0
