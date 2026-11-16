"""Custom bilingual (Arabic / English) word-level tokenizer with normalization."""
import json
import re
from collections import Counter

PAD, UNK, CLS = "<pad>", "<unk>", "<cls>"
_DIACRITICS = re.compile(r"[ً-ْـ]")  # tashkeel + tatweel
_TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def normalize(text: str) -> str:
    text = _DIACRITICS.sub("", text.lower())
    text = re.sub("[إأآا]", "ا", text)
    text = text.replace("ى", "ي").replace("ة", "ه")
    return text


def split_words(text: str) -> list[str]:
    tokens = []
    for tok in _TOKEN_RE.findall(normalize(text)):
        # Numbers carry no intent signal; collapse them to one token.
        tokens.append("<num>" if tok.isdigit() else tok)
    return tokens


class SadahTokenizer:
    def __init__(self, vocab: dict[str, int] | None = None, max_len: int = 32):
        self.vocab = vocab or {PAD: 0, UNK: 1, CLS: 2}
        self.max_len = max_len

    @property
    def pad_id(self) -> int:
        return self.vocab[PAD]

    def fit(self, texts: list[str], min_freq: int = 1) -> "SadahTokenizer":
        counts = Counter(tok for t in texts for tok in split_words(t))
        for tok, freq in counts.most_common():
            if freq >= min_freq and tok not in self.vocab:
                self.vocab[tok] = len(self.vocab)
        return self

    def encode(self, text: str, max_len: int | None = None) -> list[int]:
        limit = max_len or self.max_len
        ids = [self.vocab[CLS]]
        ids += [self.vocab.get(t, self.vocab[UNK]) for t in split_words(text)]
        ids = ids[:limit]
        return ids + [self.pad_id] * (limit - len(ids))

    def to_json(self) -> str:
        return json.dumps({"vocab": self.vocab, "max_len": self.max_len}, ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str) -> "SadahTokenizer":
        data = json.loads(raw)
        return cls(data["vocab"], data["max_len"])
