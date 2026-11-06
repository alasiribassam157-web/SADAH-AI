"""Print sample continuations from a training checkpoint, to see how the generative brain writes.

Kaggle (CPU is enough, no GPU hours):  python gpu/sample_gpt.py
Same prompts and seed every time, so two checkpoints can be compared line by line.
"""
import argparse
import glob
import sys
import time
from pathlib import Path

import torch
from tokenizers import Tokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.gpt import NexusGPT  # noqa: E402

PROMPTS = ["عاصمة المملكة العربية السعودية هي", "الذكاء الاصطناعي هو", "في عام 1945", "تقع مدينة مكة المكرمة",
           "كرة القدم هي", "The capital of France is", "القهوة العربية", "مرحبا، كيف حالك؟"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="/kaggle/input/**/ckpt.pt")
    ap.add_argument("--tokenizer", default="/kaggle/input/**/tokenizer.json")
    ap.add_argument("--max-new", type=int, default=100)
    ap.add_argument("--temperature", type=float, default=0.8)
    args = ap.parse_args()

    ckpt = glob.glob(args.ckpt, recursive=True)[0]
    state = torch.load(ckpt, map_location="cpu", weights_only=False)
    print(f"{ckpt}  step {state['step']}", flush=True)
    model = NexusGPT(**state["config"])
    model.load_state_dict(state["model"])
    model.eval()
    del state  # the optimizer state is half the file; free it before generating
    tok = Tokenizer.from_file(glob.glob(args.tokenizer, recursive=True)[0])
    stop = tok.token_to_id("<|endoftext|>")

    for prompt in PROMPTS:
        torch.manual_seed(0)
        t0 = time.time()
        with torch.no_grad():
            out = model.generate(torch.tensor([tok.encode(prompt).ids]), max_new=args.max_new,
                                 temperature=args.temperature, stop_id=stop)
        print(f">> {prompt}\n{tok.decode(out[0].tolist())}\n{time.time() - t0:.0f} sec {'-' * 30}", flush=True)


if __name__ == "__main__":
    main()
