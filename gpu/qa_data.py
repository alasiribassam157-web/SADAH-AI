"""Question → answer examples for the generative brain, built from Arabic Wikipedia (human-written text).

Each article gives one pair: a question about its title, answered by the article's own opening sentences,
wrapped in the chat tokens the tokenizer already reserves:
    <|user|>ما هي الرياض؟<|assistant|>الرياض هي عاصمة المملكة العربية السعودية …<|endoftext|>
Mixed into training (20% by default) so the brain learns to answer a question directly and on topic,
instead of continuing it like an article. Every 200th pair is held out (qa_val.bin) to measure that skill.
Test:  python -m gpu.qa_data --out /kaggle/working/qa_test --pairs 2000
"""
import argparse
import re
from collections import Counter
from pathlib import Path

import numpy as np
import torch

_PARENS = re.compile(r"\s*[(（][^()（）]{0,150}[)）]")
_SENTENCE_END = re.compile(r"(?<=[.!؟?])\s+")
_PERSON = re.compile(r"(ولد|وُلد|مواليد|توفي|تُوفي|المتوفى)")
_SKIP_TITLE = re.compile(r"^(قائمة|تصنيف|بوابة|ويكيبيديا|قالب)|توضيح|[:/0-9]")
_ARABIC = re.compile(r"[\u0621-\u064A]{2}")  # titles must be Arabic words (skips «A», «F»…)


def make_pair(title: str, text: str) -> tuple[str, str] | None:
    """(question, answer) from one article, or None when the article is a list, stub or badly formed."""
    title = title.strip()
    if not title or len(title) > 40 or _SKIP_TITLE.search(title) or not _ARABIC.search(title):
        return None
    lead = _PARENS.sub("", text.strip().split("\n", 1)[0]).strip()
    if not lead.startswith(title.split()[0]):  # the opening sentence must be about the title
        return None
    answer = ""
    for sentence in _SENTENCE_END.split(lead):
        answer = f"{answer} {sentence}".strip()
        if len(answer) >= 80:
            break
    if not 40 <= len(answer) <= 400:
        return None
    head = answer[len(title):len(title) + 30]
    if _PERSON.search(answer[:200]):
        question = f"من هي {title}؟" if " هي " in head else f"من هو {title}؟"
    elif " هي " in head:
        question = f"ما هي {title}؟"
    elif " هو " in head:
        question = f"ما هو {title}؟"
    else:
        question = f"ماذا تعرف عن {title}؟"
    return question, answer


def pairs(limit: int, per_pattern: int = 150):
    """Stream Arabic Wikipedia; at most `per_pattern` articles that open the same way (bot-made stubs)."""
    from datasets import load_dataset
    seen: Counter = Counter()
    count = 0
    for row in load_dataset("wikimedia/wikipedia", "20231101.ar", split="train", streaming=True):
        pair = make_pair(row["title"], row["text"])
        if not pair:
            continue
        pattern = " ".join(pair[1][len(row["title"]):].split()[:3])
        seen[pattern] += 1
        if seen[pattern] > per_pattern:
            continue
        yield pair
        count += 1
        if count >= limit:
            return


def build(out: Path, limit: int = 300_000) -> None:
    """Write qa.bin / qa_val.bin (token ids) and qa_starts.npy (where each training pair begins)."""
    if (out / "qa.bin").exists() or limit <= 0:
        return
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(str(out / "tokenizer.json"))
    print(f"building up to {limit:,} question-answer pairs from Arabic Wikipedia...", flush=True)
    texts = [f"<|user|>{q}<|assistant|>{a}<|endoftext|>" for q, a in pairs(limit)]
    encoded = [np.array(e.ids, dtype=np.uint16) for e in tok.encode_batch(texts)]
    val = [e for i, e in enumerate(encoded) if i % 200 == 0]
    train = [e for i, e in enumerate(encoded) if i % 200 != 0]
    starts = np.concatenate([[0], np.cumsum([len(e) for e in train])[:-1]]).astype(np.int64)
    np.concatenate(train).tofile(out / "qa.bin")
    np.concatenate(val).tofile(out / "qa_val.bin")
    np.save(out / "qa_starts.npy", starts)
    print(f"qa pairs: {len(texts):,}  tokens: train {int(starts[-1]) + len(train[-1]):,}  "
          f"val {sum(len(e) for e in val):,}", flush=True)
    examples = texts[:5]
    for e in examples:
        print("  example:", e[:160], flush=True)


def batches(path: Path, context: int, batch: int, device: str, starts: np.ndarray | None = None):
    """Random windows of `context` tokens; with `starts`, every window begins at a question."""
    data = np.memmap(path, dtype=np.uint16, mode="r")
    top = len(data) - context - 1
    while True:
        if starts is None:
            ix = np.random.randint(0, top, batch)
        else:
            ix = np.minimum(starts[np.random.randint(0, len(starts), batch)], top)
        x = torch.from_numpy(np.stack([data[i:i + context] for i in ix]).astype(np.int64))
        y = torch.from_numpy(np.stack([data[i + 1:i + 1 + context] for i in ix]).astype(np.int64))
        yield x.to(device, non_blocking=True), y.to(device, non_blocking=True)


def mixed(out: Path, share: float, context: int, batch: int, device: str):
    """Wikipedia text, with `share` of the micro-batches taken from the question-answer pairs."""
    text = batches(out / "train.bin", context, batch, device)
    if share <= 0 or not (out / "qa.bin").exists():
        yield from text
        return
    qa = batches(out / "qa.bin", context, batch, device, np.load(out / "qa_starts.npy"))
    while True:
        yield next(qa) if np.random.rand() < share else next(text)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--tokenizer", default="/kaggle/input/**/tokenizer.json")
    ap.add_argument("--pairs", type=int, default=2000)
    args = ap.parse_args()
    target = Path(args.out)
    target.mkdir(parents=True, exist_ok=True)
    if not (target / "tokenizer.json").exists():
        import glob
        import shutil
        shutil.copy(glob.glob(args.tokenizer, recursive=True)[0], target / "tokenizer.json")
    build(target, args.pairs)
