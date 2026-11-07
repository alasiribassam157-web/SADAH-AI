"""Train the SADAH generative brain from scratch on a GPU (Kaggle / Colab / rented), resumable.

Kaggle:  python -m gpu.train_gpt --size small --hours 11.5
Kaggle T4 x2 (both GPUs):  torchrun --nproc_per_node=2 -m gpu.train_gpt --size large --hours 11.5
Laptop:  python -m gpu.train_gpt --size tiny --local --steps 30        (pipeline smoke test)
Saves ckpt.pt + tokenizer.json in --out every few minutes and when the time budget ends, so the
next session continues where this one stopped (attach the previous output as input data).
--qa-share mixes question→answer pairs from Wikipedia (gpu/qa_data.py) so the brain learns to answer.
"""
import argparse
import glob
import math
import shutil
import time
from pathlib import Path

import numpy as np
import torch

from core.gpt import SIZES, NexusGPT
from gpu import multi_gpu, qa_data
from gpu.data import build


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
    ap.add_argument("--out", default="/kaggle/working/nexus_gpt" if Path("/kaggle").exists() else "checkpoints/gpt")
    ap.add_argument("--hours", type=float, default=11.5)
    ap.add_argument("--steps", type=int, default=30_000)       # where the learning rate finishes its decay
    ap.add_argument("--batch", type=int, default=2)           # Reduced from 4 to 2 to fit "large" on T4
    ap.add_argument("--accum", type=int, default=64)          # Increased to maintain effective batch size
    ap.add_argument("--context", type=int, default=512)
    ap.add_argument("--lr", type=float, default=6e-4)
    ap.add_argument("--local", action="store_true")
    ap.add_argument("--qa-share", type=float, default=0.2)      # share of micro-batches that are Q→A pairs
    ap.add_argument("--qa-pairs", type=int, default=300_000)
    ap.add_argument("--val-batches", type=int, default=200)
    ap.add_argument("--val-every", type=int, default=500)
    ap.add_argument("--no-checkpoint", action="store_true", help="disable gradient checkpointing (uses more VRAM)")
    args = ap.parse_args()

    ddp, rank, world, device = multi_gpu.setup()
    main_proc = rank == 0
    out = Path(args.out)
    resume = find_resume(out)
    if main_proc and resume and resume.parent != out:  # same tokenizer + data as last session
        out.mkdir(parents=True, exist_ok=True)
        for name in ("tokenizer.json", "train.bin", "val.bin", "qa.bin", "qa_val.bin", "qa_starts.npy"):
            if (resume.parent / name).exists() and not (out / name).exists():
                shutil.copy(resume.parent / name, out / name)
    if main_proc:
        info = build(out, local=args.local)
        qa_data.build(out, args.qa_pairs if args.qa_share > 0 else 0)
    multi_gpu.barrier(ddp)  # other GPUs wait until GPU 0 has the data ready, then just read it
    if not main_proc:
        info = build(out, local=args.local)
    accum = max(1, args.accum // world)  # same effective batch, split across GPUs
    np.random.seed(rank * 1000 + int(time.time()) % 1000)
    # recomputes activations during backward instead of storing them — trades ~30% more compute
    # for much less VRAM, which is what lets "large" (350M) fit on a 16GB T4
    grad_checkpoint = device.startswith("cuda") and not args.no_checkpoint
    print("Loading model onto device...", flush=True)
    model = NexusGPT(info["vocab"], context=args.context, grad_checkpoint=grad_checkpoint,
                     **SIZES[args.size]).to(device)
    print("Model loaded successfully.", flush=True)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, betas=(0.9, 0.95), weight_decay=0.1)
    step = 0
    if resume:
        state = torch.load(resume, map_location=device)
        model.load_state_dict(state["model"])
        opt.load_state_dict(state["opt"])
        step = state["step"]
        if main_proc:
            print(f"resumed from {resume} at step {step}")
        del state
    raw, model = model, multi_gpu.wrap(model, ddp)
    if main_proc:
        print(f"NEXUS-GPT {args.size}: {raw.params():,} parameters, {world} GPU(s)", flush=True)

    use_amp = device.startswith("cuda")
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)
    train = qa_data.mixed(out, args.qa_share, args.context, args.batch, device)
    val = qa_data.batches(out / "val.bin", args.context, args.batch, device)
    has_qa = (out / "qa_val.bin").exists()
    qa_val = qa_data.batches(out / "qa_val.bin", args.context, args.batch, device) if has_qa else None
    warmup, deadline, last_save = 1000, time.time() + args.hours * 3600, time.time()

    def lr_at(s: int) -> float:
        if s < warmup:
            return args.lr * s / warmup
        return args.lr * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * min(1.0, s / args.steps))))

    def save(tag: str) -> None:
        if not main_proc:
            return
        torch.save({"model": raw.state_dict(), "opt": opt.state_dict(), "step": step,
                    "config": raw.config, "size": args.size}, out / "ckpt.pt")
        print(f"  saved ({tag}) at step {step}", flush=True)

    if main_proc:
        print("Training loop started (accumulating gradients)...", flush=True)
    model.train()
    t0 = time.time()
    while not multi_gpu.agree_stop(step >= args.steps or time.time() >= deadline, ddp, device):
        for g in opt.param_groups:
            g["lr"] = lr_at(step)
        for i in range(accum):
            x, y = next(train)
            model.require_backward_grad_sync = not ddp or i == accum - 1  # sync once per step
            with torch.autocast("cuda" if use_amp else "cpu", dtype=torch.float16, enabled=use_amp):
                _, loss = model(x, y)
            scaler.scale(loss / accum).backward()
        scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scaler.step(opt)
        scaler.update()
        opt.zero_grad(set_to_none=True)
        step += 1
        if step % 10 == 0 and main_proc:
            tok_s = 10 * accum * world * args.batch * args.context / (time.time() - t0)
            print(f"step {step}  loss {loss.item():.3f}  lr {lr_at(step):.2e}  {tok_s:,.0f} tok/s", flush=True)
            t0 = time.time()
        if step % args.val_every == 0 and main_proc:  # GPU 0 only, on the unwrapped model (no GPU sync)
            raw.eval()
            with torch.no_grad(), torch.autocast("cuda" if use_amp else "cpu", dtype=torch.float16, enabled=use_amp):
                vl = sum(raw(*next(val))[1].item() for _ in range(args.val_batches)) / args.val_batches
                qa = sum(raw(*next(qa_val))[1].item() for _ in range(args.val_batches // 4)) / max(1, args.val_batches // 4) if has_qa else 0
            print(f"  val loss {vl:.3f}  (perplexity {math.exp(vl):.1f})  qa val loss {qa:.3f}", flush=True)
            raw.train()
        if time.time() - last_save > 1200:   # every 20 minutes: a crash never loses more than that
            save("periodic")
            last_save = time.time()
    save("final")
    multi_gpu.finish(ddp)


if __name__ == "__main__":
    main()
