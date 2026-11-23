"""How people really write a request: emoji and stretched letters, English words for the thing they want, and a correction in the middle
(«ابغى موقع لا بالاصح متجر»). The result is the text the rules read; the project name is still taken from the original words."""
import re

from builder.norm import n

_EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍]")
_STRETCH = re.compile(r"([ء-ي])\1{2,}")   # «ابغااااا» -> «ابغا»; a doubled letter is real Arabic, three or more is emphasis
_ENGLISH = [(re.compile(rf"(?<![a-z]){w}(?![a-z])", re.I), ar) for w, ar in (
    (r"web\s?site", "موقع"), (r"webpage", "موقع"), (r"landing\s?page", "صفحة هبوط"), (r"apps?", "تطبيق"), (r"blog", "مدونة"),
    (r"online\s?store|e-?shop|shop|store", "متجر"), (r"game", "لعبة"), (r"dark\s?mode", "ثيم داكن"), (r"dashboard", "لوحة"))]
_SITE = re.compile(r"(?<![ء-ي])(?:ويب\s+)?سايت(?![ء-ي])")
_FIX = re.compile(r"(?<![ء-ي])(?:لا\s+)?(?:بالاصح|بالأصح|بل|اقصد|أقصد)(?![ء-ي])")
_NAME = re.compile(r"(?<![ء-ي])(?:باسم|اسمه|اسمها|واسمه|واسمها|اسم)(?![ء-ي])")


def clean(text: str) -> str:
    """The request without emoji, and with a correction applied: only what comes after «لا بالاصح / اقصد» counts, plus the name given before it."""
    text = " ".join(_EMOJI.sub(" ", text).split())
    parts = _FIX.split(text)
    if len(parts) > 1:
        before, after = " ".join(parts[:-1]).strip(), parts[-1].strip()
        if after and not _NAME.search(after) and (m := _NAME.search(before)):
            after += " " + before[m.start():]
        text = after or text
    return text.strip()


def read(norm: str) -> str:
    """The normalised request in the words the rules know: no stretched letters, English words in Arabic."""
    norm = _STRETCH.sub(r"\1", norm)
    for rx, ar in _ENGLISH:
        norm = rx.sub(n(ar), norm)
    return _SITE.sub("موقع", norm)
