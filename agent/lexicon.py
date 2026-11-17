"""The system's whole vocabulary in one place — what SADAH considers a real word.

It is filled at start-up from the two brains' own BPE vocabularies (the 8000 learned pieces, whole
words only), the 45 programming tasks and the six language names.  `fix()` then corrects *any*
misspelled word against all of it, instead of a hand-written list of special cases.
"""
import gzip
import json
import re

from agent import arabic
from agent.code_kb import LANGS, TASKS
from agent.kb import KB_FILE

MIN_WORD = 4          # shorter pieces are too ambiguous to be correction targets
MIN_TYPO = 5          # a word must be this long before we dare change it
EVERYDAY = 0.85       # how common a word must be to correct another one into it
_WORDS: set[str] = set()
_COMMON: dict[str, float] = {}   # word -> 0…1, how early the BPE vocabulary learned it
_BY_LETTER: dict[str, list[str]] = {}   # first letter -> its words, so a lookup scans a fraction of them
_corpus_read = False


def add(text: str, common: float = 1.0) -> None:
    for word in arabic.words(text):
        clean = arabic.norm(word)
        if len(clean) >= MIN_WORD:
            if clean not in _WORDS:
                _WORDS.add(clean)
                _BY_LETTER.setdefault(clean[0], []).append(clean)
            _COMMON[clean] = max(_COMMON.get(clean, 0.0), common)


def learn(vocab: dict) -> None:
    """Take the whole BPE vocabulary of a brain: pieces that are complete words («بايثون», «الطباعة»).
    Its order is its frequency — piece 580 is an everyday word, piece 6500 is rare."""
    total = max(len(vocab), 1)
    for piece, index in vocab.items():
        if piece.endswith("</w>") and not piece.startswith("<"):
            add(piece[:-4], 1.0 - index / total)


def _seed() -> None:
    for ar, en in TASKS.values():
        add(f"{ar} {en}")
    for name, *_ in LANGS.values():
        add(name)
    add("بايثون جافا جافاسكريبت سي شارب بلس جو كوتلن سويفت روبي")


_seed()


def read_corpus() -> None:
    """Add every word of the offline library (≈32 000 real Arabic words) — once, in a fraction of a second.
    Without it the vocabulary is too small to tell a typo from a word SADAH simply has not met yet."""
    global _corpus_read
    if _corpus_read:
        return
    _corpus_read = True
    try:
        with gzip.open(KB_FILE, "rt", encoding="utf-8") as file:
            for line in file:
                article = json.loads(line)
                text = article["title"] + " " + " ".join(p for _, ps in article["sections"] for p in ps)
                for word in re.findall(r"[\u0600-\u06ff]{4,}", text):
                    add(word, 0.3)
    except (OSError, EOFError, ValueError, KeyError):
        pass


def known(word: str) -> bool:
    """A word SADAH has seen.  A long stem counts too («المصباح» ← «مصباح»), a short one does not:
    «باتون» must not pass as a word just because «بات» exists."""
    read_corpus()
    clean = arabic.norm(word)
    if not arabic.is_arabic(clean) or clean in _WORDS:
        return True
    return len(stem := arabic.stem(word)) >= 4 and stem in _WORDS


def size() -> int:
    return len(_WORDS)


def fix(word: str) -> str:
    """Correct one unknown word against the entire vocabulary.  Known words are never touched, and an
    unknown one is only replaced when there is real evidence of a typo: a repeated letter («الذكااء»),
    or a target that is one of SADAH's own everyday words («بايثن» -> «بايثون»).  A word the lexicon
    simply has never met («كريستيانو») is left exactly as written."""
    clean = arabic.norm(word)
    if len(clean) < MIN_TYPO or known(word):
        return word
    hit = arabic.closest(clean, _BY_LETTER.get(clean[0], ()), common=lambda w: _COMMON.get(w, 0.0))
    mistyped = arabic.squeeze(clean) != clean
    return hit if hit and (mistyped or _COMMON.get(hit, 0.0) >= EVERYDAY) else word


def correct(text: str) -> str:
    """Correct every unknown word in a sentence, keeping its punctuation and order."""
    out = []
    for token in text.split():
        core = token.strip("؟?!.،,:;()«»\"'")
        if not core:
            out.append(token)
            continue
        fixed = fix(core)
        out.append(token.replace(core, fixed, 1) if fixed != core else token)
    return " ".join(out)


def task_by_root(question: str) -> str | None:
    """The programming task whose title shares the most roots with the question («يرتب مصفوفة» -> sort_list)."""
    asked = arabic.roots(question) | {w.lower() for w in arabic.words(question) if not arabic.is_arabic(w)}
    best, score = None, 0
    for key, (ar, en) in TASKS.items():
        hits = len(asked & (arabic.roots(ar) | {w.lower() for w in arabic.words(en)}))
        if hits > score:
            best, score = key, hits
    return best


def supports(question: str, task: str) -> bool:
    """True when the question really mentions what this task is about — used to trust a hesitant brain."""
    ar, en = TASKS[task]
    asked = arabic.roots(question) | {w.lower() for w in arabic.words(question) if not arabic.is_arabic(w)}
    return bool(asked & (arabic.roots(ar) | {w.lower() for w in arabic.words(en)}))
