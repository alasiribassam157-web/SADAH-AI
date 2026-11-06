"""Check the NumPy brains (used on Vercel) against the PyTorch ones, then the server without PyTorch.

Run where PyTorch is installed:  py -m tests.numpy_parity
1. router + coder: same top label and near-identical logits on every benchmark question
2. app.py imports with PyTorch blocked, as on Vercel, and answers through the NumPy brains
The full benchmark on the NumPy brains:  NEXUS_NUMPY=1 py -m tests.benchmark
"""
import subprocess
import sys

import numpy as np
import torch

from core.fast_brain import NumpyBrain, load_checkpoint
from core.inference import BrainInference
from tests.benchmark_cases import CASES_V3
from tests.benchmark_cases_v4 import CASES_V4
from tests.benchmark_cases_v5 import CASES_V5
from tests.benchmark_cases_v6 import CASES_V6

BLOCK_TORCH = "import sys; sys.modules['torch'] = None; "


def compare(brain: str, questions: list[str]) -> bool:
    ref = BrainInference(brain)
    ckpt = load_checkpoint(ref.path)
    fast = NumpyBrain(ckpt["config"], ckpt["state_dict"])
    same, worst = 0, 0.0
    for q in questions:
        ids = ref.tok.encode(q)
        with torch.no_grad():
            a = ref.model(torch.tensor([ids], dtype=torch.long))[0].numpy()
        b = fast(ids)
        same += int(a.argmax() == b.argmax())
        worst = max(worst, float(np.abs(a - b).max()))
    ok = same == len(questions) and worst < 1e-3
    print(f"{brain}: same label {same}/{len(questions)}, largest logit difference {worst:.2e}  {'OK' if ok else 'FAIL'}")
    return ok


def server_without_torch() -> bool:
    code = BLOCK_TORCH + ("import app; b = app.agent.brain; r = app.agent.handle('كم 100 دولار بالريال؟'); "
                          "print(b.info['backend'], app.dev_api is None, r['intent'])")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    last = (out.stdout.strip().splitlines() or [""])[-1]
    print("server without PyTorch:", last or out.stderr.strip()[-600:])
    return out.returncode == 0 and last.startswith("numpy True")


if __name__ == "__main__":
    questions = [case[0] for case in CASES_V3 + CASES_V4 + CASES_V5 + CASES_V6]
    results = [compare("router", questions), compare("coder", questions), server_without_torch()]
    print("ALL OK" if all(results) else "FAILED")
    sys.exit(0 if all(results) else 1)
