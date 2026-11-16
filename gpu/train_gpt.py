"""Train the SADAH generative brain from scratch on a GPU (Kaggle / Colab / rented), resumable.

Kaggle:  python -m gpu.train_gpt --size small --hours 11.5
Laptop:  python -m gpu.train_gpt --size tiny --local --steps 30        (pipeline smoke test)
Saves ckpt.pt + tokenizer.json in --out every few minutes and when the time budget ends, so the
next session continues where this one stopped (attach the previous output as input data).
"""
import argparse
import glob
import math
import shutil
import time
from pathlib import Path

import numpy as np
import torch

from core.gpt import SIZES, SadahGPT
from gpu.data import build


def batches(path: Path, context: int, batch: int, device: str):
    data = np.memmap(path, dtype=np.uint16, mode="r")
    while True:
        ix = np.random.randint(0, len(data) - context - 1, batch)
        x = torch.from_numpy(np.stack([data[i:i + context] for i in ix]).astype(np.int64))
        y = torch.from_numpy(np.stack([data[i + 1:i + 1 + context] for i in ix]).astype(np.int64))
        yield x.to(device, non_blocking=True), y.to(device, non_blocking=True)


def find_resume(out: Path) -> Path | None:
    """This session's checkpoint, or one from a previous session attached under /kaggle/input."""
    own = out / "ckpt.pt"
    if own.exists():
        return own
    found = sorted(glob.glob("/kaggle/input/**/ckpt.pt", recursive=True))
    return Path(found[-1]) if found else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", default="small", choices=list(SIZES))
    ap.add_argument("--out", default="/kaggle/working/sadah_gpt" if Path("/kaggle").exists() else "checkpoints/gpt")
    ap.add_argument("--hours", type=float, default=11.5)
    ap.add_argument("--steps", type=int, default=200_000)
    ap.add_argument("--batch", type=int, default=2)           # Reduced from 4 to 2 to fit "large" on T4
    ap.add_argument("--accum", type=int, default=64)          # Increased to maintain effective batch size
    ap.add_argument("--context", type=int, default=512)
    ap.add_argument("--lr", type=float, default=6e-4)
    ap.add_argument("--local", action="store_true")
    ap.add_argument("--no-checkpoint", action="store_true", help="disable gradient checkpointing (uses more VRAM)")
    args = ap.parse_args()

    out = Path(args.out)
    resume = find_resume(out)
    if resume and resume.parent != out:  # bring last session's tokenizer + data so ids stay identical
        out.mkdir(parents=True, exist_ok=True)
        for name in ("tokenizer.json", "train.bin", "val.bin"):
            if (resume.parent / name).exists() and not (out / name).exists():
                shutil.copy(resume.parent / name, out / name)
    info = build(out, local=args.local)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    # recomputes activations during backward instead of storing them — trades ~30% more compute
    # for much less VRAM, which is what lets "large" (350M) fit on a 16GB T4
    grad_checkpoint = device == "cuda" and not args.no_checkpoint
    print("Loading model onto device...", flush=True)
    model = SadahGPT(info["vocab"], context=args.context, grad_checkpoint=grad_checkpoint,
                     **SIZES[args.size]).to(device)
    print("Model loaded successfully.", flush=True)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, betas=(0.9, 0.95), weight_decay=0.1)
    step = 0
    if resume:
        state = torch.load(resume, map_location=device)
        model.load_state_dict(state["model"])
        opt.load_state_dict(state["opt"])
        step = state["step"]
        print(f"resumed from {resume} at step {step}")
    print(f"SADAH-GPT {args.size}: {model.params():,} parameters on {device}")

    use_amp = device == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)
    train = batches(out / "train.bin", args.context, args.batch, device)
    val = batches(out / "val.bin", args.context, args.batch, device)
    warmup, deadline, last_save = 1000, time.time() + args.hours * 3600, time.time()

    def lr_at(s: int) -> float:
        if s < warmup:
            return args.lr * s / warmup
        return args.lr * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * min(1.0, s / args.steps))))

    def save(tag: str) -> None:
        torch.save({"model": model.state_dict(), "opt": opt.state_dict(), "step": step,
                    "config": model.config, "size": args.size}, out / "ckpt.pt")
        print(f"  saved ({tag}) at step {step}", flush=True)

    print("Training loop started (accumulating gradients)...", flush=True)
    model.train()
    t0 = time.time()
    while step < args.steps and time.time() < deadline:
        for g in opt.param_groups:
            g["lr"] = lr_at(step)
        for _ in range(args.accum):
            x, y = next(train)
            with torch.autocast(device, dtype=torch.float16, enabled=use_amp):
                _, loss = model(x, y)
            scaler.scale(loss / args.accum).backward()
        scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scaler.step(opt)
        scaler.update()
        opt.zero_grad(set_to_none=True)
        step += 1
        if step % 10 == 0:  # Changed from 50 to 10 so you see progress much faster
            tok_s = 10 * args.accum * args.batch * args.context / (time.time() - t0)
            print(f"step {step}  loss {loss.item():.3f}  lr {lr_at(step):.2e}  {tok_s:,.0f} tok/s", flush=True)
            t0 = time.time()
        if step % 500 == 0:
            model.eval()
            with torch.no_grad(), torch.autocast(device, dtype=torch.float16, enabled=use_amp):
                vl = sum(model(*next(val))[1].item() for _ in range(20)) / 20
            print(f"  val loss {vl:.3f}  (perplexity {math.exp(vl):.1f})", flush=True)
            model.train()
        if time.time() - last_save > 1200:   # every 20 minutes: a crash never loses more than that
            save("periodic")
            last_save = time.time()
    save("final")


if __name__ == "__main__":
    main()
