"""Collect plain-text Wikipedia paragraphs for self-supervised pre-training (SADAH v5).

Run:  py -m core.corpus ar 250     ->  data/corpus/ar.txt
      py -m core.corpus en 150     ->  data/corpus/en.txt
Most-viewed articles first (the topics people actually ask about), then random articles for breadth.
"""
import re
import sys
import time
from pathlib import Path

import httpx

CORPUS = Path(__file__).resolve().parent.parent / "data" / "corpus"
HEADERS = {"User-Agent": "SADAH-Agent/1.0 (https://github.com/alasiribassam157-web/SADAH-AI) python-httpx"}
_CLUTTER = re.compile(r"\s*\([^()]*\)")            # pronunciations and dates in brackets
_DIACRITICS = re.compile(r"[ً-ْٰـ]")
MIN_CHARS = 60


def _api(http: httpx.Client, lang: str, params: dict) -> dict:
    base = {"action": "query", "format": "json", "prop": "extracts", "exintro": 1, "explaintext": 1, "exlimit": 20}
    return http.get(f"https://{lang}.wikipedia.org/w/api.php", params={**base, **params}).json()


def _paragraphs(pages: dict) -> list[str]:
    out = []
    for page in pages.values():
        text = _DIACRITICS.sub("", _CLUTTER.sub("", page.get("extract", "")))
        out += [" ".join(p.split()) for p in text.split("\n") if len(p.strip()) >= MIN_CHARS]
    return out


def _most_viewed(http: httpx.Client, lang: str) -> list[str]:
    data = http.get(f"https://{lang}.wikipedia.org/w/api.php", params={
        "action": "query", "format": "json", "list": "mostviewed", "pvimlimit": 500}).json()
    return [p["title"] for p in data.get("query", {}).get("mostviewed", []) if ":" not in p["title"]]


def collect(lang: str, random_requests: int, pause: float = 0.25) -> int:
    CORPUS.mkdir(parents=True, exist_ok=True)
    out = CORPUS / f"{lang}.txt"
    seen = set(out.read_text(encoding="utf-8").splitlines()) if out.exists() else set()
    written = 0
    with httpx.Client(timeout=30, headers=HEADERS) as http, out.open("a", encoding="utf-8") as f:
        def save(paragraphs: list[str]) -> None:
            nonlocal written
            for p in paragraphs:
                if p not in seen:
                    seen.add(p)
                    f.write(p + "\n")
                    written += 1

        titles = _most_viewed(http, lang)
        for i in range(0, len(titles), 20):
            try:
                save(_paragraphs(_api(http, lang, {"titles": "|".join(titles[i:i + 20])})["query"]["pages"]))
            except (httpx.HTTPError, KeyError, ValueError):
                time.sleep(2)
            time.sleep(pause)
        print(f"[{lang}] most-viewed: {len(titles)} articles, {written} paragraphs", flush=True)

        for i in range(random_requests):
            try:
                pages = _api(http, lang, {"generator": "random", "grnnamespace": 0, "grnlimit": 20})["query"]["pages"]
                save(_paragraphs(pages))
            except (httpx.HTTPError, KeyError, ValueError):
                time.sleep(2)
            if i % 25 == 0:
                print(f"[{lang}] random {i}/{random_requests}: {written} paragraphs", flush=True)
            time.sleep(pause)
    size_mb = out.stat().st_size / 1e6
    print(f"[{lang}] done: +{written} paragraphs, {out.name} = {size_mb:.1f} MB", flush=True)
    return written


if __name__ == "__main__":
    collect(sys.argv[1] if len(sys.argv) > 1 else "ar", int(sys.argv[2]) if len(sys.argv) > 2 else 250)
