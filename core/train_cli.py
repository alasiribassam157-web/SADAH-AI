"""Command line of core.trainer: train a candidate, run the regression gate, optionally promote it.

    py -m core.trainer router pretrained 12                      train, then show the gate's verdict
    py -m core.trainer router pretrained 12 --promote            ...and make it the served brain if the gate passes
    py -m core.trainer --experiment add-skill-x                  take brain/size/epochs from the saved experiment
"""
import argparse
import json
import sys

from core import lifecycle, trainer
from core.dataset_builder import BRAINS
from core.registry import Registry, RegistryError


def _print(m: dict) -> None:
    print(f"[{m['brain']}] epoch {m['epoch']:>2}/{m['epochs']}  loss {m['loss']:.4f}  acc {m['acc']:.3f}"
          f"  val_acc {m['val_acc']:.3f}  ({m['elapsed']}s)", flush=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m core.trainer", description=__doc__.split("\n")[0])
    ap.add_argument("which", nargs="?", default=None, help="router | coder | all")
    ap.add_argument("size", nargs="?", default=None, help="small | medium | large | xlarge | pretrained")
    ap.add_argument("epochs", nargs="?", type=int, default=None)
    ap.add_argument("--experiment", default="", help="name created by `core.lifecycle new-experiment`")
    ap.add_argument("--promote", action="store_true", help="promote the candidate when the gate passes")
    ap.add_argument("--no-review", action="store_true", help="only store the candidate, skip the gate")
    a = ap.parse_args(argv)
    reg, cfg = Registry(), {}
    if a.experiment:
        path = reg.root / "experiments" / f"{a.experiment}.json"
        if not path.exists():
            sys.exit(f"unknown experiment '{a.experiment}': create it with `python -m core.lifecycle new-experiment`")
        cfg = json.loads(path.read_text(encoding="utf-8"))
    which, size = a.which or cfg.get("brain", "all"), a.size or cfg.get("size", "medium")
    epochs, code = a.epochs or cfg.get("epochs", 12), 0
    for name in (BRAINS if which == "all" else [which]):
        r = trainer.train(brain=name, size=size, epochs=epochs, on_epoch=_print, experiment=a.experiment)
        print(f"{name} candidate v{r['registry_version']} stored  params={r['params']:,}  steps={r['steps']}"
              f"  val_acc={r['val_acc']}  time={r['seconds']}s" + ("  (STOPPED by the time cap)" if r["truncated"] else ""))
        if a.no_review:
            continue
        try:
            if a.promote:
                verdict = lifecycle.review_and_promote(name, r["registry_version"], reg)
            else:
                verdict = lifecycle.review(name, r["registry_version"], reg)
        except RegistryError as exc:
            print(f"gate not run: {exc}")
            code = 2
            continue
        print(lifecycle.gate.render(verdict))
        print(f"{name} v{r['registry_version']}: " + ("PROMOTED" if a.promote and verdict["passed"] else
              "passed the gate; run `python -m core.lifecycle promote %s %d`" % (name, r["registry_version"])
              if verdict["passed"] else "REJECTED, the stable brain is unchanged"))
        code = code or (0 if verdict["passed"] else 1)
    return code


if __name__ == "__main__":
    sys.exit(main())
