"""Shop products and prices from a request: «وفيه بخور 50 ودهن عود 200» -> [("بخور", 50), ("دهن عود", 200)].
Each price closes one product; its name is the words since the last «فيه / وفيه / ونبيع / :» (at most three words,
one when there is no such marker). Phone numbers and e-mails are already out of the text (builder.facts)."""
import re

from builder.norm import n

_CUT = {n(w) for w in ("فيه", "فيها", "وفيه", "وفيها", "نبيع", "ونبيع", "منتجاتنا", "ومنتجاتنا", "باسم", "اسمه", "اسمها", "واسمه")}
_MONEY = {n(w) for w in ("ريال", "ريالات", "ر.س", "رس", "دينار", "درهم", "دولار")}
_NUM = re.compile(r"\d+(?:\.\d+)?")
_ARABIC = re.compile(r"^[ء-ي]+$")


def products(text: str) -> list[tuple[str, float]]:
    out, words = [], []
    for tok in text.split():
        bare = tok.strip("،,.؛!؟")
        if _NUM.fullmatch(bare):
            name = _name(words, first=not out)
            if name:
                out.append((name, float(bare)))
            words = []
        elif n(bare) not in _MONEY and bare:
            words.append(tok)
            if tok.endswith(":"):
                words = []
    return out


def _name(words: list[str], first: bool) -> str:
    cut = max((i for i, w in enumerate(words) if n(w.strip("،,.")) in _CUT), default=-1)
    seg = [w.strip("،,.:") for w in words[cut + 1:]]
    seg = seg[-1:] if first and cut < 0 else seg[-3:]   # the opening words of a request are not a product name
    if seg and seg[0].startswith("و") and len(seg[0]) > 3:
        seg[0] = seg[0][1:]   # «ودهن» -> «دهن»
    return " ".join(w for w in seg if _ARABIC.match(w))
