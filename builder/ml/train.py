"""Train the design model:  python -m builder.ml.train  [--check]

Builds the training set from builder/ml/corpus_a.py and corpus_b.py (every business noun in several carrier sentences, some with the kind of noise
real typing has), trains builder/ml/nb.py on it and writes builder/ml/weights.json. Deterministic: the same corpus gives the same file byte for byte,
so a test can check that the shipped weights are exactly what this script produces. `--check` only compares and reports."""
import json
import random
import sys
from pathlib import Path

from builder.ml import nb
from builder.ml.corpus_a import A
from builder.ml.corpus_b import B
from builder.ml.corpus_c import C

WEIGHTS = Path(__file__).with_name("weights.json")
CARRIERS = ["موقع {}", "ابغى موقع {}", "ابي {}", "عندي {} وابغى له موقع", "{} باسم", "متجر {}", "سوي لي موقع {}", "ودي بصفحة {}", "{}", "ابغى شي {}",
            "مشروعي {}", "صفحة تعريفية {}", "{} عندنا", "بغيت اسوي موقع {}", "اعمل لي موقع {}", "تصميم موقع {}"]
NAMES = ["الريان", "نجمة", "الامل", "سما", "الفجر", "قمر", "الرواد", "ميراث", "افق", "ركن", "ضياء", "المدى", "سلسبيل", "نور", "غيم", "وهج"]   # carry no kind: the model must not learn them


def lam(x: str) -> str:
    return "لل" + x[2:] if x.startswith("ال") else "ل" + x


def noisy(text: str, rnd: random.Random) -> str:
    """One typing slip: a dropped, doubled or swapped letter, or a spelling variant (ة/ه, ى/ي, أ/ا)."""
    words = text.split()
    i = rnd.randrange(len(words))
    w = words[i]
    kind = rnd.randrange(5)
    if kind == 0 and len(w) > 3:
        j = rnd.randrange(1, len(w))
        w = w[:j] + w[j + 1:]
    elif kind == 1 and len(w) > 2:
        j = rnd.randrange(len(w))
        w = w[:j] + w[j] + w[j:]
    elif kind == 2 and len(w) > 3:
        j = rnd.randrange(1, len(w) - 1)
        w = w[:j] + w[j + 1] + w[j] + w[j + 2:]
    else:
        w = w.replace("ة", "ه").replace("ى", "ي").replace("أ", "ا")
    words[i] = w
    return " ".join(words)


def samples(per_noun: int = 10, seed: int = 11) -> list[tuple[str, str]]:
    rnd = random.Random(seed)
    out = []
    for kind, nouns in sorted({**A, **B}.items()):
        words = [x.strip() for x in C[kind].split("،") if x.strip()]
        for noun in [x.strip() for x in nouns.split("،") if x.strip()] + words:
            for _ in range(per_noun):
                car = rnd.choice(CARRIERS)
                if noun not in words and rnd.random() < .3:   # a name of the business with a word about what it does
                    noun_used = f"{noun} {rnd.choice(words)}"
                else:
                    noun_used = noun
                text = car.format(lam(noun_used) if car.endswith(" {}") and rnd.random() < .5 else noun_used)
                if rnd.random() < .4:
                    text += " باسم " + rnd.choice(NAMES)
                if rnd.random() < .35:
                    text = noisy(text, rnd)
                out.append((text, kind))
    return out


def build() -> dict:
    return nb.train(samples())


def dump(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


if __name__ == "__main__":
    text = dump(build())
    if "--check" in sys.argv:
        print("same" if WEIGHTS.read_text(encoding="utf-8") == text else "DIFFERENT")
    else:
        WEIGHTS.write_text(text, encoding="utf-8")
        print(f"wrote {WEIGHTS.name}: {len(text) // 1024} KB")
