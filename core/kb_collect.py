"""Download the knowledge library: full Wikipedia articles (English + Arabic) for core/kb_topics.py.

Run:  py -m core.kb_collect        ->  data/kb/kb.jsonl.gz   (shipped with the app, ~3 MB)
Each line: {"domain", "lang", "title", "url", "sections": [[heading, [paragraphs]], ...]}
Text is Wikipedia's (CC BY-SA); every answer links back to its article.
"""
import gzip
import json
import re
import time
from pathlib import Path

import httpx

from core.kb_topics import DOMAINS

OUT = Path(__file__).resolve().parent.parent / "data" / "kb" / "kb.jsonl.gz"
HEADERS = {"User-Agent": "SADAH-Agent/1.0 (https://github.com/alasiribassam157-web/SADAH-AI) python-httpx"}
MAX_CHARS = 16_000
SKIP = re.compile(r"^(references|see also|external links|further reading|notes|bibliography|sources|"
                  r"citations|المراجع|مراجع|انظر أيضا|انظر أيضًا|وصلات خارجية|روابط خارجية|مصادر|ملاحظات|"
                  r"قراءات إضافية|المصادر)$", re.I)
_CLUTTER = re.compile(r"\s*\([^()]*\)")
_DIACRITICS = re.compile(r"[ً-ْٰـ]")


def _sections(text: str) -> list:
    """Split '== Heading ==' plain text into [[heading, [paragraphs]]], dropping reference sections."""
    out, heading, paras, skipping, total = [], "", [], False, 0
    for line in text.split("\n"):
        m = re.match(r"^=+\s*(.*?)\s*=+$", line.strip())
        if m:
            if paras and not skipping:
                out.append([heading, paras])
            heading, paras = m.group(1), []
            skipping = bool(SKIP.match(heading))
            continue
        line = " ".join(_DIACRITICS.sub("", _CLUTTER.sub("", line)).split())
        if len(line) >= 50 and not skipping and total < MAX_CHARS:
            paras.append(line)
            total += len(line)
    if paras and not skipping:
        out.append([heading, paras])
    return out


def _article(http: httpx.Client, lang: str, title: str) -> dict | None:
    data = http.get(f"https://{lang}.wikipedia.org/w/api.php", params={
        "action": "query", "format": "json", "redirects": 1, "titles": title, "prop": "extracts|info|langlinks",
        "explaintext": 1, "inprop": "url", "lllang": "ar", "lllimit": 1}).json()
    page = next(iter(data.get("query", {}).get("pages", {}).values()), {})
    if "missing" in page or not page.get("extract"):
        return None
    ar_title = (page.get("langlinks") or [{}])[0].get("*")
    return {"lang": lang, "title": page["title"], "url": page.get("fullurl", ""),
            "sections": _sections(page["extract"]), "ar_title": ar_title}


def collect(pause: float = 0.3) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    count, chars = 0, 0
    with httpx.Client(timeout=30, headers=HEADERS) as http, gzip.open(OUT, "wt", encoding="utf-8") as f:
        for domain, titles in DOMAINS.items():
            for title in titles:
                try:
                    en = _article(http, "en", title)
                    ar = _article(http, "ar", en["ar_title"]) if en and en["ar_title"] else None
                except (httpx.HTTPError, ValueError) as exc:
                    print(f"  ! {title}: {exc}")
                    continue
                for art in (en, ar):
                    if art and art["sections"]:
                        art.pop("ar_title", None)
                        f.write(json.dumps({"domain": domain, **art}, ensure_ascii=False) + "\n")
                        count += 1
                        chars += sum(len(p) for _, ps in art["sections"] for p in ps)
                print(f"[{domain}] {title}  ->  en {'ok' if en else '-'}  ar {ar['title'] if ar else '-'}")
                time.sleep(pause)
    print(f"\nknowledge library: {count} articles, {chars:,} characters  ->  {OUT}")


if __name__ == "__main__":
    collect()
