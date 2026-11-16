"""Synthetic bilingual training data for both brains, plus the developer's taught corrections."""
import json
import random
from pathlib import Path

from core import templates_code, templates_router

INTENTS = templates_router.INTENTS
CUSTOM_FILE = Path(__file__).resolve().parent.parent / "data" / "custom_examples.jsonl"
CUSTOM_WEIGHT = 8
TYPO_RATE = 0.12  # share of examples that get one realistic spelling mistake
# Self-training from real usage (questions archived on the laptop by the developer dashboard)
ARCHIVE = CUSTOM_FILE.with_name("cloud_questions.jsonl")
AUTO_WEIGHT, CRITIC_WEIGHT = 2, 4

# brain name -> (labels, templates, slots, examples per label)
BRAINS = {
    "router": (templates_router.INTENTS, templates_router.TEMPLATES, templates_router.SLOTS, 4000),
    "coder": (templates_code.CODE_TASKS, templates_code.TEMPLATES, templates_code.SLOTS, 700),
}

_PREFIXES = ["", "", "", "", "please ", "can you ", "sadah ", "من فضلك ", "لو سمحت ", "ابغى ", "ابي ", "i want to ",
             "hey ", "يا sadah ", "سؤال: ", "quick question: "]
_SUFFIXES = ["", "", "", "", " please", " now", " ?", "؟", " الان", " بسرعة", " لو سمحت", " الله يعافيك", " thanks", "!"]


def _fill(template: str, slots: dict, rng: random.Random) -> str:
    out = template
    for slot, values in slots.items():
        token = "{" + slot + "}"
        while token in out:
            out = out.replace(token, rng.choice(values), 1)
    return " ".join(out.split())


def _typo(text: str, rng: random.Random) -> str:
    """Swap, drop or double one letter in a longer word: «الطقس» -> «الطفس» / «الطس» / «الطققس»."""
    words = text.split()
    long_words = [i for i, w in enumerate(words) if len(w) >= 4 and w.isalpha()]
    if not long_words:
        return text
    i = rng.choice(long_words)
    w, j = words[i], rng.randrange(1, len(words[i]) - 1)
    kind = rng.random()
    if kind < 0.4:
        w = w[:j] + w[j + 1] + w[j] + w[j + 2:]
    elif kind < 0.7:
        w = w[:j] + w[j + 1:]
    else:
        w = w[:j] + w[j] + w[j:]
    words[i] = w
    return " ".join(words)


def load_custom(brain: str = "router") -> list[dict]:
    """Examples the developer taught from the dashboard (data/custom_examples.jsonl)."""
    if not CUSTOM_FILE.exists():
        return []
    labels = BRAINS[brain][0]
    rows = [json.loads(line) for line in CUSTOM_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [r for r in rows if r.get("brain", "router") == brain and r.get("intent") in labels]


def add_custom(text: str, label: str, brain: str = "router") -> int:
    if label not in BRAINS[brain][0]:
        raise ValueError(f"Unknown label for {brain}: {label}")
    CUSTOM_FILE.parent.mkdir(exist_ok=True)
    row = {"text": text.strip(), "intent": label}
    if brain != "router":
        row["brain"] = brain
    with CUSTOM_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(load_custom(brain))


def load_auto_labels() -> list[tuple[str, str, int]]:
    """(text, intent, weight) learned without a human: confident verified answers, and — weighted higher —
    the cases where the critic corrected the brain. Held-out test questions are never used."""
    if not ARCHIVE.exists():
        return []
    try:
        from tests.heldout import HELDOUT
        exclude = {q for qs in HELDOUT.values() for q in qs}
    except ImportError:
        exclude = set()
    out = []
    for line in ARCHIVE.read_text(encoding="utf-8").splitlines():
        r = json.loads(line) if line.strip() else {}
        if not r.get("ok") or r.get("intent") not in INTENTS or not r.get("neural") or r.get("text") in exclude:
            continue
        if r["neural"] != r["intent"]:
            out.append((r["text"], r["intent"], CRITIC_WEIGHT))
        elif (r.get("confidence") or 0) >= 0.9:
            out.append((r["text"], r["intent"], AUTO_WEIGHT))
    return out


def build_dataset(brain: str = "router", seed: int = 7) -> tuple[list[tuple[str, int]], int]:
    """Return (shuffled (text, label) pairs, number of taught examples)."""
    labels, templates, slots, per_label = BRAINS[brain]
    rng = random.Random(seed)
    data = []
    for label, name in enumerate(labels):
        for _ in range(per_label):
            text = rng.choice(_PREFIXES) + _fill(rng.choice(templates[name]), slots, rng) + rng.choice(_SUFFIXES)
            if rng.random() < TYPO_RATE:
                text = _typo(text, rng)
            data.append((text.strip(), label))
    custom = load_custom(brain)
    for row in custom:
        # Oversample taught examples so a handful of corrections actually move the model.
        data += [(row["text"], labels.index(row["intent"]))] * CUSTOM_WEIGHT
    if brain == "router":
        for text, intent, weight in load_auto_labels():
            data += [(text, labels.index(intent))] * weight
    rng.shuffle(data)
    return data, len(custom)


def train_val_split(data: list, val_ratio: float = 0.15):
    cut = int(len(data) * (1 - val_ratio))
    return data[:cut], data[cut:]


if __name__ == "__main__":
    for brain_name, (names, *_rest) in BRAINS.items():
        sample, _ = build_dataset(brain_name)
        print(f"== {brain_name}: {len(sample)} examples")
        for text, label in sample[:5]:
            print(f"{names[label]:>14} | {text}")
