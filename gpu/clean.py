"""Cleaning for the generative brain's text: normalisation, quality filters, near-duplicate removal, leak guard.

Pure Python, no network. Order matters: normalise -> filter -> leak check -> de-duplicate.
Human-written text only; nothing here calls a model.
"""
import hashlib
import re
import unicodedata

_TATWEEL = "ـ"
_INVISIBLE = re.compile("[​-‏‪-‮⁦-⁩﻿]")
_SPACES = re.compile(r"[ \t ]+")
_BLANKS = re.compile(r"\n{3,}")
_URL = re.compile(r"https?://\S+|www\.\S+")
_WORD = re.compile(r"\w+", re.UNICODE)


def normalize(text: str) -> str:
    """NFKC (folds Arabic presentation forms), no tatweel/invisible marks, tidy spaces and blank lines."""
    text = unicodedata.normalize("NFKC", text).replace(_TATWEEL, "")
    text = _INVISIBLE.sub("", text)
    text = "\n".join(_SPACES.sub(" ", line).strip() for line in text.split("\n"))
    return _BLANKS.sub("\n\n", text).strip()


def arabic_share(text: str) -> float:
    """Fraction of letters that are Arabic (0 when there are no letters)."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum("؀" <= c <= "ۿ" or "ݐ" <= c <= "ݿ" for c in letters) / len(letters)


def quality_ok(text: str, min_chars: int = 40, min_arabic: float = 0.0, max_url_share: float = 0.2,
               max_symbol_share: float = 0.3, max_repeat: float = 0.5) -> bool:
    """Reject too-short, link-heavy, symbol-heavy or loop-like text; min_arabic>0 keeps Arabic-dominant text."""
    if len(text) < min_chars or arabic_share(text) < min_arabic:
        return False
    if sum(len(m) for m in _URL.findall(text)) > max_url_share * len(text):
        return False
    if sum(not (c.isalnum() or c.isspace()) for c in text) > max_symbol_share * len(text):
        return False
    words = _WORD.findall(text)
    return not words or len(set(words)) >= (1 - max_repeat) * len(words)


def words(text: str) -> list[str]:
    return _WORD.findall(text.casefold())


def _grams(text: str, n: int):
    w = words(text)
    return [" ".join(w[i:i + n]) for i in range(max(len(w) - n + 1, 1))] if w else []


class LeakGuard:
    """Flags text that shares a word n-gram with any held-out evaluation question (keeps tests unseen)."""

    def __init__(self, questions, n: int = 6):
        self.n, self.grams = n, set()
        for q in questions:
            w = words(q)
            if len(w) >= 4:  # shorter questions are too generic to guard without dropping good text
                self.grams.update(_grams(q, min(n, len(w))))
        self.sizes = sorted({len(g.split()) for g in self.grams}, reverse=True)

    def leaks(self, text: str) -> bool:
        w = words(text)
        for size in self.sizes:
            if any(" ".join(w[i:i + size]) in self.grams for i in range(len(w) - size + 1)):
                return True
        return False


def _simhash(text: str, n: int = 4) -> int:
    acc = [0] * 64
    for g in _grams(text, n):
        h = int.from_bytes(hashlib.blake2b(g.encode(), digest_size=8).digest(), "big")
        for bit in range(64):
            acc[bit] += 1 if (h >> bit) & 1 else -1
    return sum(1 << b for b in range(64) if acc[b] > 0)


class Deduper:
    """Drops exact and near-duplicate documents (simhash, 4 bands of 16 bits, Hamming distance <= max_dist)."""

    def __init__(self, max_dist: int = 3):
        self.max_dist, self.bands = max_dist, [{} for _ in range(4)]

    def seen(self, text: str) -> bool:
        """True if text is (near) a document already added; otherwise remembers it and returns False."""
        h = _simhash(text)
        keys = [(h >> (16 * i)) & 0xFFFF for i in range(4)]
        for band, key in zip(self.bands, keys):
            if any(bin(h ^ other).count("1") <= self.max_dist for other in band.get(key, ())):
                return True
        for band, key in zip(self.bands, keys):
            band.setdefault(key, []).append(h)
        return False


def pipeline(texts, guard: LeakGuard | None = None, min_arabic: float = 0.0, stats: dict | None = None):
    """Yield clean, unique, leak-free documents; `stats` (if given) counts what was dropped and why."""
    stats = stats if stats is not None else {}
    dedupe = Deduper()
    for raw in texts:
        text = normalize(raw)
        reason = ("quality" if not quality_ok(text, min_arabic=min_arabic)
                  else "leak" if guard and guard.leaks(text)
                  else "duplicate" if dedupe.seen(text) else "")
        stats[reason or "kept"] = stats.get(reason or "kept", 0) + 1
        if not reason:
            yield text
