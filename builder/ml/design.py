"""The design assistant: reads what the project is about with the trained model, and suggests (and can apply) the look that suits it.

  suggest(spec)  -> Suggestion or None     none when the model is not sure enough (confidence below MIN) or the text says nothing about a business
  apply(spec, s) -> Spec                   the same project with the suggested colour and look
  names(text, seed) -> [str]               names that fit the kind of business the text is about
  wants(nt)      -> bool                   the person asked for it («اختر لي تصميم مناسب», «صمم بذكاء»)"""
import json
import re
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path

from builder.ml import nb, profiles
from builder.spec import DEFAULT_ACCENT, Spec

MIN = 0.5   # measured on held-out phrases: at or above this the kind was right about 9 times in 10 (tests/ml_test.py)
_WANTS = re.compile(r"(?<![ء-ي])(?:اختر|اختار|اقترح|حدد|صمم)\s+(?:لي\s+)?(?:انت\s+)?(?:ال)?(?:تصميم|لون|شكل|ستايل|مظهر)|(?:تصميم|لون|شكل|ستايل)\s+(?:ال)?(?:مناسب|يناسب)|بذكاء|(?:انت|انتا)\s+(?:اختر|اختار)")
_GENERIC = ["نبراس", "ركن", "لمسة", "واحة", "اساس", "بصمة"]


@dataclass(frozen=True)
class Suggestion:
    kind: str
    label: str
    accent: str
    theme: str
    why: str
    because: tuple
    confidence: float


@lru_cache(maxsize=1)
def model() -> nb.Model:
    return nb.Model(json.loads(Path(__file__).with_name("weights.json").read_text(encoding="utf-8")))


def classify(text: str):
    """(kind, confidence, words that decided) for a text, or None when the model knows none of its words."""
    got = model().predict(text)
    if not got:
        return None
    kind, conf = got[0]
    return kind, conf, tuple(model().because(text, kind))


def about(spec: Spec, text: str = "") -> str:
    """What to read to tell the kind of business: the request itself without the project's name, else what the spec kept (business, items)."""
    if text.strip():
        return text.replace(spec.name, " ") if spec.name else text
    return spec.business or " ".join([spec.name, *spec.services, *(i[0] for i in spec.items)])


def suggest(spec: Spec, text: str = "") -> Suggestion | None:
    if spec.kind in ("webapp", "game"):   # a to-do app or a snake game has no business to dress
        return None
    got = classify(about(spec, text))
    if not got or got[1] < MIN:
        return None
    kind, conf, because = got
    label, accent, theme, why = profiles.P[kind]
    return Suggestion(kind, label, accent, theme, why, because, conf)


def apply(spec: Spec, s: Suggestion) -> Spec:
    return replace(spec, accent=s.accent, theme=s.theme)


def decided(spec: Spec) -> bool:
    """True when the person already chose a colour or a look: the assistant then keeps out."""
    return spec.accent != DEFAULT_ACCENT or spec.theme != "default"


def wants(nt: str) -> bool:
    return bool(_WANTS.search(nt))


def names(text: str, seed: str = "") -> list[str]:
    got = classify(text)
    pool = profiles.names(got[0]) if got and got[1] >= 0.35 else _GENERIC
    start = sum(map(ord, seed)) % len(pool)
    return [pool[(start + i * 5) % len(pool)] for i in range(3)]
