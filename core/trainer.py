"""CPU-friendly training loop for SADAH brains (time cap, limited threads).

Run directly:  py -m core.trainer [router|coder|all] [small|medium|large|xlarge] [epochs]
Trained weights live in models/ and are committed, so the cloud serves the exact brain you tested.
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import Callable

import torch
import torch.nn as nn

from core import finetune
from core.dataset_builder import BRAINS, build_dataset, train_val_split
from core.neural_net import SadahBrain
from core.tokenizer import SadahTokenizer

MODELS = Path(__file__).resolve().parent.parent / "models"
VERSIONS = MODELS / "versions.json"
MAX_SECONDS = float(os.getenv("SADAH_MAX_TRAIN_SECONDS", "2700"))  # per brain; protects the laptop
CPU_THREADS = 2      # keep CPU load (and heat) low
# Goals agreed with the developer: ~1M (SADAH v2), ~2.5M (SADAH v3), then ~5M (SADAH v4).
TARGET_PARAMS = 5_000_000
SIZES = {
    "small": dict(d_model=64, n_heads=4, n_layers=2, d_ff=128),
    "medium": dict(d_model=128, n_heads=4, n_layers=3, d_ff=256),
    "large": dict(d_model=192, n_heads=6, n_layers=4, d_ff=384),
    "xlarge": dict(d_model=256, n_heads=8, n_layers=6, d_ff=512),
}


def checkpoint(brain: str) -> Path:
    return MODELS / f"{brain}.pt"


def load_versions() -> list[dict]:
    try:
        return json.loads(VERSIONS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def _tensors(pairs, tok):
    x = torch.tensor([tok.encode(t, 32) for t, _ in pairs], dtype=torch.long)
    y = torch.tensor([label for _, label in pairs], dtype=torch.long)
    return x, y


@torch.no_grad()
def _evaluate(model, x, y, loss_fn):
    model.eval()
    logits = model(x)
    return loss_fn(logits, y).item(), (logits.argmax(-1) == y).float().mean().item()


def train(brain: str = "router", size: str = "medium", epochs: int = 12, batch_size: int = 64, lr: float = 2e-3,
          on_epoch: Callable[[dict], None] | None = None) -> dict:
    """Train one brain and save it. `on_epoch` receives live metrics for the dashboard."""
    torch.set_num_threads(CPU_THREADS)
    torch.manual_seed(0)
    start = time.time()
    labels = BRAINS[brain][0]

    data, n_custom = build_dataset(brain)
    train_pairs, val_pairs = train_val_split(data)
    extra = {}
    if size == "pretrained":
        # Transfer learning: start from the encoder that learned the language from Wikipedia.
        model, tok, extra = finetune.load_pretrained(len(labels))
        lr = min(lr, 5e-4)
    else:
        # min_freq=2 keeps one-off typos out of the vocabulary; the brain learns to read them as <unk>.
        tok = SadahTokenizer(max_len=32).fit([t for t, _ in train_pairs], min_freq=2)
        model = SadahBrain(len(tok.vocab), len(labels), max_len=tok.max_len, pad_id=tok.pad_id, **SIZES[size])
    x_tr, y_tr = _tensors(train_pairs, tok)
    x_va, y_va = _tensors(val_pairs, tok)
    steps_per_epoch = (len(x_tr) + batch_size - 1) // batch_size
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=epochs * steps_per_epoch)
    loss_fn = nn.CrossEntropyLoss(label_smoothing=0.05)
    history, steps = [], 0

    for epoch in range(1, epochs + 1):
        model.train()
        perm = torch.randperm(len(x_tr))
        total, correct, loss_sum = 0, 0, 0.0
        for i in range(0, len(perm), batch_size):
            idx = perm[i:i + batch_size]
            logits = model(x_tr[idx])
            loss = loss_fn(logits, y_tr[idx])
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            steps += 1
            loss_sum += loss.item() * len(idx)
            correct += (logits.argmax(-1) == y_tr[idx]).sum().item()
            total += len(idx)

        val_loss, val_acc = _evaluate(model, x_va, y_va, loss_fn)
        metrics = {"brain": brain, "epoch": epoch, "epochs": epochs, "loss": round(loss_sum / total, 4),
                   "acc": round(correct / total, 4), "val_loss": round(val_loss, 4),
                   "val_acc": round(val_acc, 4), "elapsed": round(time.time() - start, 2)}
        history.append(metrics)
        if on_epoch:
            on_epoch(metrics)
        if time.time() - start > MAX_SECONDS:
            break

    versions = load_versions()
    info = {"version": len(versions) + 1, "brain": brain, "size": size,
            "params": sum(p.numel() for p in model.parameters()), "steps": steps,
            "total_steps": steps + sum(v["steps"] for v in versions), "examples": len(train_pairs),
            "custom_examples": n_custom, "vocab": len(tok.vocab), "labels": len(labels),
            "val_acc": history[-1]["val_acc"], "seconds": round(time.time() - start, 2),
            "date": time.strftime("%Y-%m-%d %H:%M"), "tokenizer": getattr(tok, "kind", "word"), **extra}
    MODELS.mkdir(parents=True, exist_ok=True)
    # fp16 halves the file size on GitHub; inference converts back to fp32.
    weights = {k: v.half() if v.is_floating_point() else v for k, v in model.state_dict().items()}
    torch.save({"state_dict": weights, "config": model.config, "tokenizer": tok.to_json(),
                "intents": labels, "history": history, "info": info}, checkpoint(brain))
    VERSIONS.write_text(json.dumps(versions + [info], indent=1), encoding="utf-8")
    return {"history": history, "checkpoint": str(checkpoint(brain)), **info}


if __name__ == "__main__":
    def _print(m):
        print(f"[{m['brain']}] epoch {m['epoch']:>2}/{m['epochs']}  loss {m['loss']:.4f}  acc {m['acc']:.3f}"
              f"  val_acc {m['val_acc']:.3f}  ({m['elapsed']}s)", flush=True)

    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    size = sys.argv[2] if len(sys.argv) > 2 else "medium"
    epochs = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    for name in (BRAINS if which == "all" else [which]):
        result = train(brain=name, size=size, epochs=epochs, on_epoch=_print)
        print(f"{name} v{result['version']} saved  params={result['params']:,}  steps={result['steps']}"
              f"  val_acc={result['val_acc']}  time={result['seconds']}s")
