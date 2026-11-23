"""A multinomial naive Bayes text classifier on character n-grams, in plain Python: the whole «AI» of the design assistant.

Why this and not rules: it learns from examples which word pieces point to which label, so a business it never saw («مطعم تايلندي») is still
placed by the pieces it shares with ones it did (مطعم), misspellings and dialect spellings still share most pieces, and it can say which words
decided. Why this and not a neural net: it trains in seconds, the whole model is a small JSON file, it needs no library, and it is exactly reproducible."""
import math
import re

from builder.norm import n

SIZES = (2, 3, 4)
_AR = re.compile(r"[^ء-ي]")
# words of the request itself, not of the business: left out, in training and in use, so «ابغى موقع» never points anywhere
FILLER = {n(w) for w in ("ابغى ابي ابغا ودي بغيت اريد عندي عندنا احتاج نحتاج يبي يبغى ابغاه اسوي سوي سوه اعمل اعملي صمم اهلا هلا مرحبا السلام عليكم "
                         "موقع صفحه صفحة تطبيق متجر مشروع مشروعي باسم اسمه على في من الى لي له لها لنا عن الانترنت النت اون لاين اونلاين وابغى وابي وعندي "
                         "ممكن لو سمحت شي شيء كذا الكتروني الكترونية الكترونيه الكتروني يحتاج تحتاج اصمم تصميم بيع محل").split()}


def feats(text: str) -> list[str]:
    """The word and its edge-marked 2-4 letter pieces, for every Arabic word of the (normalised) text."""
    out = []
    for w in n(text).replace("ـ", "").split():
        w = _AR.sub("", w)
        if len(w) < 2 or w in FILLER:
            continue
        out.append("w:" + w)
        p = f"^{w}$"
        for k in SIZES:
            out += [p[i:i + k] for i in range(len(p) - k + 1)]
    return out


def train(samples: list[tuple[str, str]], min_count: int = 2, alpha: float = 0.3) -> dict:
    """samples: (text, label). Returns the model as plain data (JSON-able, deterministic)."""
    labels = sorted({y for _, y in samples})
    index = {y: i for i, y in enumerate(labels)}
    counts: dict[str, dict[int, int]] = {}
    docs = [0] * len(labels)
    for text, y in samples:
        docs[index[y]] += 1
        for f in feats(text):
            row = counts.setdefault(f, {})
            row[index[y]] = row.get(index[y], 0) + 1
    kept = {f: r for f, r in counts.items() if sum(r.values()) >= min_count}
    totals = [0] * len(labels)
    for r in kept.values():
        for i, c in r.items():
            totals[i] += c
    return {"labels": labels, "docs": docs, "totals": totals, "alpha": alpha, "vocab": len(kept),
            "counts": {f: {str(i): c for i, c in sorted(r.items())} for f, r in sorted(kept.items())}}


class Model:
    def __init__(self, data: dict):
        self.labels, self.alpha = data["labels"], data["alpha"]
        total_docs = sum(data["docs"])
        self.prior = [math.log(d / total_docs) for d in data["docs"]]
        denom = [t + self.alpha * data["vocab"] for t in data["totals"]]
        self.logp = {f: [math.log((r.get(str(i), 0) + self.alpha) / denom[i]) for i in range(len(self.labels))] for f, r in data["counts"].items()}

    def scores(self, text: str) -> tuple[list[float], int]:
        """Per-label log score of the text, and how many of its pieces the model knows."""
        s, used = list(self.prior), 0
        for f in feats(text):
            if f in self.logp:
                used += 1
                s = [a + b for a, b in zip(s, self.logp[f])]
        return s, used

    def predict(self, text: str) -> list[tuple[str, float]]:
        """Labels with a confidence, best first. The confidence is a softmax of the average score per known piece (naive Bayes alone is far
        too sure of itself because it treats overlapping pieces as independent); an unknown text has none and returns an empty list."""
        s, used = self.scores(text)
        if used == 0:
            return []
        z = [(v - self.prior[i]) / used * 4 + self.prior[i] for i, v in enumerate(s)]
        m = max(z)
        e = [math.exp(v - m) for v in z]
        tot = sum(e)
        return sorted(((self.labels[i], x / tot) for i, x in enumerate(e)), key=lambda t: -t[1])

    def because(self, text: str, label: str, top: int = 2) -> list[str]:
        """The words of the text that pushed the most toward `label` rather than toward the other labels."""
        i, out = self.labels.index(label), []
        for w in text.split():
            piece = feats(w)
            if not piece:
                continue
            gain = sum(self.logp[f][i] - sum(self.logp[f]) / len(self.labels) for f in piece if f in self.logp)
            word = _AR.sub("", w.replace("ـ", ""))
            if word.startswith("ل") and "w:" + n(word[1:]) in self.logp:   # «لمطعم» is shown as «مطعم»
                word = word[1:]
            out.append((gain, word))
        return [w for g, w in sorted(out, reverse=True)[:top] if g > 0]
