"""Byte-Pair-Encoding tokenizer trained from scratch (SADAH v5).

Words are split into learned sub-word pieces, so unseen words, typos and dialect forms still map to
known parts: «والمدرسة» -> «وال», «مدرس», «ة</w>». Same interface as core.tokenizer.SadahTokenizer.
"""
import heapq
import json
from collections import Counter, defaultdict

from core.tokenizer import split_words

SPECIAL = ["<pad>", "<unk>", "<cls>", "<mask>", "<num>"]
END = "</w>"  # marks the last piece of a word


class BPETokenizer:
    kind = "bpe"

    def __init__(self, merges: list | None = None, vocab: dict | None = None, max_len: int = 48):
        self.merges = [tuple(m) for m in (merges or [])]
        self.vocab = vocab or {s: i for i, s in enumerate(SPECIAL)}
        self.max_len = max_len
        self.ranks = {m: i for i, m in enumerate(self.merges)}
        self._cache: dict[str, list[str]] = {}

    @property
    def pad_id(self) -> int:
        return self.vocab["<pad>"]

    @property
    def mask_id(self) -> int:
        return self.vocab["<mask>"]

    # ---------- training ----------
    def train(self, texts, vocab_size: int = 8000, min_freq: int = 2) -> "BPETokenizer":
        counts = Counter(w for text in texts for w in split_words(text) if w not in SPECIAL)
        words = [list(w) + [END] for w, c in counts.items() if c >= min_freq]
        freqs = [counts[w] for w, c in counts.items() if c >= min_freq]
        for symbol, _ in Counter(s for word, f in zip(words, freqs) for s in word for _ in range(f)).most_common():
            self.vocab.setdefault(symbol, len(self.vocab))
        pairs, where = Counter(), defaultdict(set)
        for i, word in enumerate(words):
            for pair in zip(word, word[1:]):
                pairs[pair] += freqs[i]
                where[pair].add(i)
        heap = [(-c, p) for p, c in pairs.items()]
        heapq.heapify(heap)
        while len(self.vocab) < vocab_size and heap:
            neg, pair = heapq.heappop(heap)
            if pairs.get(pair, 0) != -neg:
                continue  # stale heap entry
            if -neg < min_freq:
                break
            merged, changed = pair[0] + pair[1], set()
            self.merges.append(pair)
            self.vocab.setdefault(merged, len(self.vocab))
            for i in list(where[pair]):
                word, f = words[i], freqs[i]
                for p in zip(word, word[1:]):
                    pairs[p] -= f
                    changed.add(p)
                new, j = [], 0
                while j < len(word):
                    if j + 1 < len(word) and (word[j], word[j + 1]) == pair:
                        new.append(merged)
                        j += 2
                    else:
                        new.append(word[j])
                        j += 1
                words[i] = new
                for p in zip(new, new[1:]):
                    pairs[p] += f
                    where[p].add(i)
                    changed.add(p)
            pairs.pop(pair, None)
            for p in changed:
                if pairs.get(p, 0) > 0:
                    heapq.heappush(heap, (-pairs[p], p))
        self.ranks = {m: i for i, m in enumerate(self.merges)}
        return self

    # ---------- encoding ----------
    def pieces(self, word: str) -> list[str]:
        if word in SPECIAL:
            return [word]
        if word in self._cache:
            return self._cache[word]
        parts = list(word) + [END]
        while len(parts) > 1:
            ranked = [(self.ranks.get((parts[i], parts[i + 1]), 1 << 30), i) for i in range(len(parts) - 1)]
            best, _ = min(ranked)
            if best == 1 << 30:
                break
            pair, new, j = self.merges[best], [], 0
            while j < len(parts):
                if j + 1 < len(parts) and (parts[j], parts[j + 1]) == pair:
                    new.append(parts[j] + parts[j + 1])
                    j += 2
                else:
                    new.append(parts[j])
                    j += 1
            parts = new
        if len(self._cache) < 200_000:
            self._cache[word] = parts
        return parts

    def tokenize(self, text: str) -> list[str]:
        return [p for w in split_words(text) for p in self.pieces(w)]

    def encode(self, text: str, max_len: int | None = None) -> list[int]:
        limit = max_len or self.max_len
        unk = self.vocab["<unk>"]
        ids = [self.vocab["<cls>"]] + [self.vocab.get(p, unk) for p in self.tokenize(text)]
        ids = ids[:limit]
        return ids + [self.pad_id] * (limit - len(ids))

    def to_json(self) -> str:
        return json.dumps({"kind": self.kind, "merges": self.merges, "vocab": self.vocab, "max_len": self.max_len},
                          ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str) -> "BPETokenizer":
        data = json.loads(raw)
        return cls(data["merges"], data["vocab"], data["max_len"])
