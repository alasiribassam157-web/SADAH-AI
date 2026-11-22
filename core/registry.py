"""Versioned store for the brains' weights: candidates are never served until the gate approves them.

Layout (see docs/OPERATIONS.md):
    models/router.pt, models/coder.pt     the STABLE weights the server loads (a copy, written atomically)
    models/registry/<brain>/vN/model.pt   every trained version (weights are git-ignored)
    models/registry/<brain>/vN/meta.json  status, sha256, training info, evaluation, gate verdict (committed)
    models/registry/<brain>/stable.json   which version is stable and the ones it replaced (for rollback)
    models/registry/<brain>/history.jsonl append-only audit log of every state change
Pure standard library: it must work on a machine without PyTorch.
"""
import hashlib
import json
import os
import shutil
import time
from pathlib import Path

MODELS = Path(__file__).resolve().parent.parent / "models"
CANDIDATE, PASSED, REJECTED, STABLE, ARCHIVED = "candidate", "gated-pass", "rejected", "stable", "archived"


class RegistryError(Exception):
    """A registry operation that cannot be done (unknown version, missing or corrupt weights)."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, data: object) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, path)


class Registry:
    def __init__(self, models_dir: Path = MODELS):
        self.models, self.root = Path(models_dir), Path(models_dir) / "registry"

    # ---- reading -------------------------------------------------------------------------------------------
    def brain_dir(self, brain: str) -> Path:
        return self.root / brain

    def versions(self, brain: str) -> list[dict]:
        found = sorted(self.brain_dir(brain).glob("v*/meta.json"), key=lambda p: int(p.parent.name[1:]))
        return [json.loads(p.read_text(encoding="utf-8")) for p in found]

    def meta(self, brain: str, version: int) -> dict:
        path = self.brain_dir(brain) / f"v{version}" / "meta.json"
        if not path.exists():
            raise RegistryError(f"{brain} has no version {version} (see: python -m core.lifecycle status)")
        return json.loads(path.read_text(encoding="utf-8"))

    def weights(self, brain: str, version: int) -> Path:
        return self.brain_dir(brain) / f"v{version}" / "model.pt"

    def stable_state(self, brain: str) -> dict:
        path = self.brain_dir(brain) / "stable.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"version": None, "previous": []}

    def stable(self, brain: str) -> int | None:
        return self.stable_state(brain)["version"]

    def served(self, brain: str) -> Path:
        return self.models / f"{brain}.pt"

    def served_matches_stable(self, brain: str) -> bool:
        """True when models/<brain>.pt is byte-identical to the registered stable version (no silent drift)."""
        version = self.stable(brain)
        return version is not None and self.served(brain).exists() and \
            sha256(self.served(brain)) == self.meta(brain, version)["sha256"]

    # ---- writing -------------------------------------------------------------------------------------------
    def _save_meta(self, brain: str, meta: dict) -> None:
        _write_json(self.brain_dir(brain) / f"v{meta['version']}" / "meta.json", meta)

    def log(self, brain: str, event: str, version: int, **extra) -> None:
        line = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "event": event, "version": version, **extra}
        with (self.brain_dir(brain) / "history.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

    def add(self, brain: str, weights: Path, info: dict, move: bool = False, status: str = CANDIDATE) -> int:
        """Store a new version next to the others; it never touches the stable weights."""
        number = max((v["version"] for v in self.versions(brain)), default=0) + 1
        folder = self.brain_dir(brain) / f"v{number}"
        folder.mkdir(parents=True)
        (shutil.move if move else shutil.copy2)(str(weights), folder / "model.pt")
        meta = {"brain": brain, "version": number, "status": status, "created": time.strftime("%Y-%m-%d %H:%M"),
                "sha256": sha256(folder / "model.pt"), "train": info, "eval": None, "gate": None}
        self._save_meta(brain, meta)
        self.log(brain, "added", number, status=status)
        return number

    def update(self, brain: str, version: int, **fields) -> dict:
        meta = {**self.meta(brain, version), **fields}
        self._save_meta(brain, meta)
        return meta

    def reject(self, brain: str, version: int, reason: str) -> None:
        if version == self.stable(brain):
            raise RegistryError(f"{brain} v{version} is the stable version; roll back to another one first")
        self.update(brain, version, status=REJECTED, reason=reason)
        self.log(brain, "rejected", version, reason=reason)

    def _install(self, brain: str, version: int) -> None:
        """Copy a version's weights to models/<brain>.pt after checking they are the ones that were registered."""
        meta, src = self.meta(brain, version), self.weights(brain, version)
        if not src.exists():
            raise RegistryError(f"weights of {brain} v{version} are not on this machine ({src}); weights are "
                                "git-ignored - restore the file or retrain")
        if sha256(src) != meta["sha256"]:
            raise RegistryError(f"{src} does not match the sha256 registered for {brain} v{version} (corrupt file)")
        tmp = self.models / f".{brain}.pt.tmp"
        shutil.copy2(src, tmp)
        os.replace(tmp, self.models / f"{brain}.pt")   # atomic: the server never reads a half-written file

    def promote(self, brain: str, version: int, via: str = "promote") -> None:
        """Make a version stable. Callers must have run the gate (core.lifecycle does)."""
        meta = self.meta(brain, version)
        if meta["status"] not in (PASSED, STABLE, ARCHIVED):
            raise RegistryError(f"{brain} v{version} is '{meta['status']}': only a version that passed the gate "
                                "can be promoted")
        state = self.stable_state(brain)
        old, state["previous"] = state["version"], [p for p in state["previous"] if p != version]
        self._install(brain, version)
        if old not in (None, version):
            self.update(brain, old, status=ARCHIVED)
            state["previous"].append(old)
        self.update(brain, version, status=STABLE, promoted=time.strftime("%Y-%m-%d %H:%M"))
        _write_json(self.brain_dir(brain) / "stable.json", {"version": version, "previous": state["previous"]})
        self.log(brain, via, version, replaced=old)

    def rollback(self, brain: str, to: int | None = None) -> int:
        """Re-install an earlier stable version (default: the one this stable replaced)."""
        state = self.stable_state(brain)
        target = to if to is not None else (state["previous"][-1] if state["previous"] else None)
        if target is None:
            raise RegistryError(f"{brain} has no earlier stable version to roll back to")
        if target == state["version"]:
            raise RegistryError(f"{brain} v{target} is already the stable version")
        if self.meta(brain, target)["status"] == REJECTED:
            raise RegistryError(f"{brain} v{target} was rejected by the gate and cannot become stable")
        self.promote(brain, target, via="rollback")
        return target
