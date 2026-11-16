"""Self-supervised pre-training (SADAH v5): the brain learns Arabic/English by filling in hidden pieces.

Run:  py -m core.pretrain [steps]        (resumes automatically from checkpoints/base_pretrain.pt)
Reads data/corpus/*.txt (Wikipedia, see core/corpus.py) plus the task templates, trains a BPE tokenizer
once, then trains a SadahMLM. The encoder later initialises the router/coder brains (transfer learning).
"""
import json
import math
import os
import sys
import time
from pathlib import Path

import torch
import torch.nn.functional as F

from core.bpe import BPETokenizer
from core.dataset_builder import BRAINS, build_dataset
from core.neural_net import SadahMLM

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "corpus"
CKPT = ROOT / "checkpoints" / "base_pretrain.pt"      # full state for resuming (gitignored)
LOG = ROOT / "checkpoints" / "pretrain_log.json"       # progress shown on the developer dashboard
BASE = dict(d_model=256, n_heads=8, n_layers=6, d_ff=1024, max_len=48, dropout=0.1)
VOCAB_SIZE, BATCH, LR, WARMUP, MASK_RATE = 8000, 32, 6e-4, 400, 0.15
MAX_HOURS = float(os.getenv("SADAH_PRETRAIN_HOURS", "6"))
CPU_THREADS = 2


def _texts() -> list[str]:
    paragraphs = []
    for path in sorted(CORPUS.glob("*.txt")):
        paragraphs += [p for p in path.read_text(encoding="utf-8").splitlines() if p.strip()]
    task = [t for brain in BRAINS for t, _ in build_dataset(brain)[0][:15000]]  # the way people ask questions
    return paragraphs + task


def _windows(tok: BPETokenizer, texts: list[str]) -> torch.Tensor:
    """Cut every text into windows of max_len pieces (first id = <cls>)."""
    cls, size, rows = tok.vocab["<cls>"], BASE["max_len"] - 1, []
    unk = tok.vocab["<unk>"]
    for text in texts:
        ids = [tok.vocab.get(p, unk) for p in tok.tokenize(text)]
        for i in range(0, max(len(ids), 1), size):
            chunk = ids[i:i + size]
            if len(chunk) >= 4:
                rows.append([cls] + chunk + [tok.pad_id] * (size - len(chunk)))
    return torch.tensor(rows, dtype=torch.long)


def mask_batch(ids: torch.Tensor, tok: BPETokenizer) -> tuple[torch.Tensor, torch.Tensor]:
    """BERT recipe: hide 15% of real pieces; 80% become <mask>, 10% a random piece, 10% stay."""
    labels = ids.clone()
    real = ids.ne(tok.pad_id) & ids.ne(tok.vocab["<cls>"])
    chosen = (torch.rand(ids.shape) < MASK_RATE) & real
    labels[~chosen] = -100
    inputs = ids.clone()
    roll = torch.rand(ids.shape)
    inputs[chosen & (roll < 0.8)] = tok.mask_id
    swap = chosen & (roll >= 0.8) & (roll < 0.9)
    inputs[swap] = torch.randint(len(tok.vocab), (int(swap.sum()),))
    return inputs, labels


def _lr(step: int, total: int) -> float:
    if step < WARMUP:
        return LR * (step + 1) / WARMUP
    progress = (step - WARMUP) / max(1, total - WARMUP)
    return LR * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * min(progress, 1.0))))


def pretrain(total_steps: int = 8000) -> dict:
    torch.set_num_threads(CPU_THREADS)
    CKPT.parent.mkdir(parents=True, exist_ok=True)
    state = torch.load(CKPT, map_location="cpu", weights_only=False) if CKPT.exists() else None
    texts = _texts()
    tok = BPETokenizer.from_json(state["tokenizer"]) if state else BPETokenizer(max_len=BASE["max_len"]).train(
        texts, vocab_size=VOCAB_SIZE)
    data = _windows(tok, texts)
    model = SadahMLM(vocab_size=len(tok.vocab), pad_id=tok.pad_id, **BASE)
    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
    step, history = 0, []
    if state:
        model.load_state_dict(state["model"])
        opt.load_state_dict(state["optimizer"])
        step, history = state["step"], state["history"]
    params = sum(p.numel() for p in model.brain.parameters())
    print(f"pre-training: {params:,} params, vocab {len(tok.vocab)}, {len(data):,} windows, step {step}/{total_steps}",
          flush=True)
    run_start = window_start = time.time()
    loss_sum, acc_sum, n = 0.0, 0.0, 0
    model.train()
    while step < total_steps:
        batch = data[torch.randint(len(data), (BATCH,))]
        inputs, labels = mask_batch(batch, tok)
        logits = model(inputs)
        loss = F.cross_entropy(logits.view(-1, logits.size(-1)), labels.view(-1), ignore_index=-100)
        for group in opt.param_groups:
            group["lr"] = _lr(step, total_steps)
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        hit = labels.ne(-100)
        acc_sum += (logits.argmax(-1)[hit] == labels[hit]).float().mean().item() if hit.any() else 0.0
        loss_sum, n, step = loss_sum + loss.item(), n + 1, step + 1
        out_of_time = time.time() - run_start > MAX_HOURS * 3600
        if step % 100 == 0 or step == total_steps or out_of_time:
            rate = n / (time.time() - window_start)
            history.append({"step": step, "loss": round(loss_sum / n, 4), "masked_acc": round(acc_sum / n, 4),
                            "time": time.strftime("%H:%M")})
            print(f"step {step}/{total_steps}  loss {loss_sum / n:.3f}  masked-acc {acc_sum / n:.1%}  "
                  f"{rate:.2f} step/s  ETA {(total_steps - step) / max(rate, 1e-6) / 60:.0f} min", flush=True)
            loss_sum, acc_sum, n, window_start = 0.0, 0.0, 0, time.time()
            torch.save({"model": model.state_dict(), "optimizer": opt.state_dict(), "step": step, "history": history,
                        "tokenizer": tok.to_json(), "config": {**BASE, "vocab_size": len(tok.vocab), "pad_id": tok.pad_id},
                        "params": params}, CKPT)
            LOG.write_text(json.dumps({"params": params, "step": step, "total": total_steps, "history": history[-200:]},
                                      ensure_ascii=False), encoding="utf-8")
        if out_of_time:
            print("time limit reached - progress saved, run again to continue", flush=True)
            break
    return {"step": step, "params": params, "history": history}


if __name__ == "__main__":
    pretrain(int(sys.argv[1]) if len(sys.argv) > 1 else 8000)
