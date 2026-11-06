"""Load a trained brain checkpoint and predict labels.

Uses PyTorch when it is installed (training, the laptop, Docker). Without it — the Vercel server, or with
NEXUS_NUMPY=1 — the same checkpoint runs on NumPy through core.fast_brain, with the same predictions.
"""
import json
import os
from pathlib import Path

import numpy as np

from core.bpe import BPETokenizer
from core.tokenizer import NexusTokenizer

try:
    if os.getenv("NEXUS_NUMPY") == "1":
        raise ImportError("NumPy backend requested")
    import torch
    import torch.nn.functional as F

    from core.neural_net import NexusBrain
except ImportError:
    torch = None
from core.fast_brain import NumpyBrain, load_checkpoint

MODELS = Path(__file__).resolve().parent.parent / "models"
BACKEND = "torch" if torch else "numpy"


def checkpoint(brain: str) -> Path:
    return MODELS / f"{brain}.pt"  # same path as core.trainer.checkpoint, without importing PyTorch


class BrainInference:
    def __init__(self, brain: str = "router"):
        self.brain = brain
        self.path: Path = checkpoint(brain)
        self.model = None
        self.tok = None
        self.intents: list[str] = []
        self.info: dict = {}
        self.reload()

    @property
    def ready(self) -> bool:
        return self.model is not None

    def reload(self) -> bool:
        if not self.path.exists():
            return False
        if torch:
            ckpt = torch.load(self.path, map_location="cpu", weights_only=True)
            model = NexusBrain(**ckpt["config"])
            model.load_state_dict(ckpt["state_dict"])
            model.eval()
            params = sum(p.numel() for p in model.parameters())
        else:
            ckpt = load_checkpoint(self.path)
            model = NumpyBrain(ckpt["config"], ckpt["state_dict"])
            params = model.params()
        self.model, self.intents = model, ckpt["intents"]
        raw = ckpt["tokenizer"]
        self.tok = (BPETokenizer if json.loads(raw).get("kind") == "bpe" else NexusTokenizer).from_json(raw)
        self.info = {**ckpt.get("info", {}), **ckpt["config"], "params": params, "backend": BACKEND}
        return True

    def predict(self, text: str) -> tuple[str, float, dict[str, float]]:
        """Return (label, confidence, full probability map)."""
        if not self.ready:
            raise RuntimeError(f"{self.brain} brain not trained yet - run core.trainer first")
        ids = self.tok.encode(text)
        if torch:
            with torch.no_grad():
                probs = F.softmax(self.model(torch.tensor([ids], dtype=torch.long)), dim=-1)[0].numpy()
        else:
            logits = self.model(ids)
            probs = np.exp(logits - logits.max())
            probs /= probs.sum()
        best = int(probs.argmax())
        dist = {name: round(float(p), 4) for name, p in zip(self.intents, probs)}
        return self.intents[best], float(probs[best]), dist
