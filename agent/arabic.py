# test line one
# test line two
"""General Arabic morphology — no word lists, no special cases.

`stem()` strips the prefixes and suffixes any Arabic word can carry, `root()` reduces a stem to its
consonant skeleton (weak letters dropped), and `dice()` compares two words by their 2/3-grams.
Everything downstream (spelling, retrieval gates, topic cores, code tasks) is built on these four.
"""
import difflib
import re

_DIACRITICS = re.compile(r"[ً-ْٰـ]")
_TRANS = str.maketrans("أإآٱىةؤئ", "اااايهوي")
_ARABIC = re.compile(r"[؀-ۿ]")
# longest first: «وبالمدرسة» loses «وبال», not «و».  Single letters other than «و» are never stripped:
# «بايثون» must not become «ايثون» and «كتابة» must not become «تابة».
PREFIXES = ("وبال", "فبال", "وال", "بال", "كال", "فال", "لل", "ال", "و")
SUFFIXES = ("اتهما", "اتهم", "اتها", "تهما", "هما", "كما", "اتك", "اتي", "ونا", "ينا", "ات", "ون",
            "ين", "ان", "ها", "هم", "هن", "كم", "كن", "نا", "ية", "يه", "ته", "ه", "ي")
_VERB_PREFIX = ("مست", "است", "ي", "ت", "ن", "ا", "م")   # يكتب / تكتب / اكتب / مكتوب -> كتب
_WEAK = str.maketrans("", "", "اويء")
MIN_STEM = 3


def is_arabic(word: str) -> bool:
    return bool(_ARABIC.search(word))


def norm(word: str) -> str:
    """Lower-case, drop tashkeel, unify hamza / ya / ta-marbuta: «مَدْرَسَة» and «مدرسه» become one word."""
    return _DIACRITICS.sub("", word.strip().lower()).translate(_TRANS)


def squeeze(word: str) -> str:
    """«ارجوككك» -> «ارجوك», «ممممتاز» -> «متاز»: three or more of the same letter collapse to one."""
    return re.sub(r"(.)\1{2,}", r"\1", word)


def strip_prefix(word: str) -> str:
    for p in PREFIXES:
        keep = 2 if p.endswith("ال") or p == "لل" else MIN_STEM   # «الرز» -> «رز»
        if word.startswith(p) and len(word) - len(p) >= keep:
            return word[len(p):]
    return word


def strip_suffix(word: str) -> str:
    for s in SUFFIXES:
        if word.endswith(s) and len(word) - len(s) >= MIN_STEM:
            return word[:-len(s)]
    return word


def stem(word: str) -> str:
    """Light stem: «والمدارس» -> «مدارس» -> «مدرس»; «السباحة» -> «سباح»; «يكتبون» -> «يكتب»."""
    word = squeeze(norm(word))
    if not is_arabic(word):
        return word[:-1] if len(word) > 4 and word.endswith("s") and not word.endswith("ss") else word
    word = strip_suffix(strip_prefix(word))
    return strip_suffix(word) if len(word) > 5 else word


def root(word: str) -> str:
    """Consonant skeleton of a stem: «ترتيب» and «يرتب» both reduce to «رتب», «كتابة» to «كتب».

    Each step keeps at least three letters, so «بيت» and «بناء» survive whole."""
    base = stem(word)
    if not is_arabic(base):
        return base
    for p in _VERB_PREFIX:
        if base.startswith(p) and len(base) - len(p) >= (2 if p in ("ي", "ت", "ن", "ا") else 3):
            base = base[len(p):]
            break
    skeleton = base.translate(_WEAK)
    # two strong letters are a real Arabic root once the weak ones drop: «بناء» and «تبنى» both give «بن»
    return skeleton if len(skeleton) >= 2 else base


def words(text: str) -> list[str]:
    return re.findall(r"[\w؀-ۿ#+]+", text)


def stems(text: str) -> set[str]:
    return {s for w in words(text) if len(s := stem(w)) >= 2}


def roots(text: str) -> set[str]:
    return {r for w in words(text) if len(r := root(w)) >= 2}


def grams(word: str) -> set[str]:
    """2-grams and 3-grams of a padded word: the fingerprint used for fuzzy matching."""
    padded = f"^{norm(word)}$"
    return {padded[i:i + n] for n in (2, 3) for i in range(len(padded) - n + 1)}


def dice(a: str, b: str) -> float:
    """Sørensen–Dice similarity of two words over their character n-grams (0 … 1)."""
    ga, gb = grams(a), grams(b)
    return 2 * len(ga & gb) / (len(ga) + len(gb)) if ga and gb else 0.0


def similarity(a: str, b: str) -> float:
    """Two independent measures agreeing: n-gram overlap and longest-common-subsequence ratio.
    The second is only worth computing when the first already shows a resemblance."""
    shared = dice(a, b)
    return 0.5 * shared + 0.5 * difflib.SequenceMatcher(None, a, b).ratio() if shared >= 0.35 else shared * 0.5


def closest(word: str, vocabulary, floor: float = 0.75, weak: float = 0.6, margin: float = 0.06,
            common=None) -> str | None:
    """The vocabulary word that looks most like `word`, or None when the evidence is not strong enough.

    Three independent safeguards keep correct words intact: the match must be close (`floor`), or a
    little less close but an everyday word (`weak` + `common` ≥ 0.85 — how early the BPE vocabulary
    learned it); and it must beat the runner-up by `margin`, so ambiguity means «leave it alone»."""
    target = norm(word)
    rank = common or (lambda w: 0.0)
    scored = sorted(((similarity(target, c), rank(c), c) for c in vocabulary
                     if abs(len(c) - len(target)) <= 3 and c[:1] == target[:1]),   # a typo keeps the first letter
                    key=lambda s: s[0] + 0.08 * s[1])
    if not scored:
        return None
    best, usual, hit = scored[-1]
    runner_up = scored[-2][0] + 0.08 * scored[-2][1] if len(scored) > 1 else 0.0
    if best + 0.08 * usual - runner_up < margin:
        return None
    return hit if best >= floor or (best >= weak and usual >= 0.85) else None


def overlap(question: str, text: str) -> int:
    """How many of the question's roots appear in `text` — the general relevance gate."""
    return len(roots(question) & roots(text))
