"""Transfer learning (SADAH v5): start the router/coder brains from the pre-trained encoder.

The encoder learned the language itself from Wikipedia (core/pretrain.py); fine-tuning only teaches it
the task, so it understands phrasings it never saw in the templates.
"""
import torch

from core.bpe import BPETokenizer
from core.neural_net import SadahBrain
from core.pretrain import CKPT


def available() -> bool:
    return CKPT.exists()


def load_pretrained(n_classes: int) -> tuple[SadahBrain, BPETokenizer, dict]:
    """Return (brain initialised from the pre-trained encoder, its BPE tokenizer, pre-training summary)."""
    state = torch.load(CKPT, map_location="cpu", weights_only=False)
    tok = BPETokenizer.from_json(state["tokenizer"])
    model = SadahBrain(n_classes=n_classes, **state["config"])
    encoder = {k.removeprefix("brain."): v for k, v in state["model"].items()
               if k.startswith("brain.") and not k.startswith("brain.head.")}
    missing, unexpected = model.load_state_dict(encoder, strict=False)
    if set(missing) - {"head.weight", "head.bias"} or unexpected:
        raise RuntimeError(f"pre-trained weights do not fit: missing={missing} unexpected={unexpected}")
    last = state["history"][-1] if state["history"] else {}
    return model, tok, {"pretrain_steps": state["step"], "pretrain_masked_acc": last.get("masked_acc")}
