"""Causal extractor: «لماذا / ليش / why» questions should be answered with reasons, not a general summary.

1. the search is widened with reason words (أسباب، عوامل، تفسير، لماذا)
2. a sentence that contains an explicit causal link (بسبب، لأن، نتيجة لـ، يعود ذلك إلى …) counts 2.5×
   in the TextRank / BM25 score, so the sentences that explain rise to the top of the answer.
Nothing is generated: the sentences are the sources' own.
"""
import re

import numpy as np

BOOST = 2.5
EXPANSION = {"ar": "أسباب عوامل تفسير لماذا", "en": "causes reasons factors explanation why"}
LINKS = re.compile(
    r"بسبب|لأن|لان\b|نتيجة\s+(?:ل|عن)|نتيجةً\s+ل|[يت]عود(?:\s+\S+){0,4}?\s+(?:إلى|الى|لـ)|"
    r"بهدف|مما\s+(?:يؤدي|أدى|ادى|يتسبب|تسبب)|يؤدي\s+(?:إلى|الى)|أدى\s+(?:إلى|الى)|نظرًا\s+ل|نظراً\s+ل|"
    r"ويرجع|[يت]رجع(?:\s+\S+){0,4}?\s+(?:إلى|الى)|السبب\s+(?:في|هو)|بفعل|جراء|جرّاء|من\s+أجل|"
    r"\bbecause\b|\bdue to\b|\bas a result\b|\bresult(?:s|ed)? (?:in|from)\b|\bleads? to\b|\bcaused? by\b|"
    r"\bowing to\b|\bthanks to\b|\bso that\b|\btherefore\b|\bthe reason\b", re.I)


def expand(topic: str, lang: str = "ar") -> str:
    """The widened search query: «أسباب عوامل تفسير لماذا الاحتباس الحراري»."""
    return f"{EXPANSION.get(lang, EXPANSION['ar'])} {topic}"


def is_causal(sentence: str) -> bool:
    return bool(LINKS.search(sentence))


def weights(items: list[str]) -> np.ndarray:
    """2.5 for a sentence with a causal link, 1.0 for the rest."""
    return np.array([BOOST if is_causal(s) else 1.0 for s in items])


def pick(items: list[str], scores: np.ndarray, n: int) -> list[int]:
    """The n sentences for the answer, in reading order: sentences with a causal link first (best score first),
    then the best of the rest.  A reason need not repeat the topic's words, so its score alone could lose to a definition."""
    order = [int(i) for i in np.argsort(-scores)]
    reasons = [i for i in order if is_causal(items[i])]
    return sorted((reasons + [i for i in order if i not in reasons])[:n])
