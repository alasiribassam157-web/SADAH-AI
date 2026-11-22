"""Shared helpers of the regression tests: real weights in a temp folder, a really degraded checkpoint, fake reports."""
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

os.environ.setdefault("SADAH_NUMPY", "1")   # the tests must run (and mean the same) without PyTorch

from core.fast_brain import load_checkpoint  # noqa: E402

REPO_MODELS = Path(__file__).resolve().parent.parent / "models"


def fresh_models(brains: tuple[str, ...] = ("router",)) -> Path:
    """A temp copy of models/ (weights only) the test may break freely. Caller removes it."""
    folder = Path(tempfile.mkdtemp(prefix="sadah-models-"))
    for brain in brains:
        shutil.copy2(REPO_MODELS / f"{brain}.pt", folder / f"{brain}.pt")
    return folder


def degrade(src: Path, dst: Path, label: str, shift: float = -30.0) -> Path:
    """A REAL regression, built without PyTorch: copy the checkpoint but push one skill's output bias far down,
    so the brain can no longer answer `label`. Returns dst."""
    ckpt = load_checkpoint(src)
    n, index = len(ckpt["intents"]), ckpt["intents"].index(label)
    with zipfile.ZipFile(src) as zin:
        targets = [i for i in zin.infolist() if "/data/" in i.filename and i.file_size == n * 2]   # head.bias, fp16
        assert len(targets) == 1, f"cannot locate head.bias ({len(targets)} candidates)"
        import numpy as np
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_STORED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == targets[0].filename:
                    bias = np.frombuffer(data, dtype=np.float16).copy()
                    bias[index] += np.float16(shift)
                    data = bias.tobytes()
                zout.writestr(item, data, compress_type=zipfile.ZIP_STORED)
    return dst


def report(skills: dict[str, tuple[int, int]], labels: list[str] | None = None, suite: str = "s") -> dict:
    """Fake evaluation report: {skill: (correct, total)} -> core.evalsuite report shape (one case per question)."""
    by_skill, cases = {}, []
    for skill, (correct, total) in skills.items():
        by_skill[skill] = {"correct": correct, "total": total}
        cases += [{"q": f"{skill}-{i}", "want": skill, "got": skill if i < correct else "other", "ok": i < correct}
                  for i in range(total)]
    done = sum(c for c, _ in skills.values())
    return {"labels": labels or list(skills), "suites": {suite: {"total": sum(t for _, t in skills.values()),
            "correct": done, "by_skill": by_skill, "cases": cases}}}
