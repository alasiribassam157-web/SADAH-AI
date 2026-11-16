"""Arabic <-> English translation: built-in dictionary first, then Wikidata labels for names and concepts."""
import re

import httpx

from agent.dictionary_ar_en import PAIRS
from agent.tools import ToolResult

API = "https://www.wikidata.org/w/api.php"
HEADERS = {"User-Agent": "SADAH-Agent/1.0 (https://github.com/alasiribassam157-web/SADAH-AI) python-httpx"}
_DIACRITICS = re.compile(r"[ً-ْـ]")


def _norm(text: str) -> str:
    text = _DIACRITICS.sub("", text.lower().strip())
    return re.sub("[إأآ]", "ا", text).replace("ة", "ه").replace("ى", "ي")


EN_TO_AR = {k: v for k, v in PAIRS.items()}
AR_TO_EN = {_norm(v): k for k, v in PAIRS.items()}

# "ترجم قطة للانجليزي" / "وش معنى cat بالعربي" / "how do you say water in arabic" / "قطة بالانجليزي"
_PATTERNS = [
    r"(?:ترجم|ترجملي|ترجم لي|translate)\s+[«\"']?(.+?)[»\"']?(?:\s+(?:الى|إلى|لل|ل|بال|to|into|in)\s*\S+)?$",
    r"(?:وش|ايش|شو|ما|ايه)\s+(?:معنى|معني)\s+(.+?)(?:\s+(?:بال|في ال|بـ)\S+)?$",
    r"(?:كيف|ازاي)\s+(?:اقول|أقول|نقول|يقولون)\s+(.+?)\s+(?:بال|بـ)\S+$",
    r"(?:شو|ايش|وش)\s+يعني\s+(.+?)(?:\s+(?:بال|بـ)\S+)?$", r"يعني\s+(?:ايه|ايش|شو)\s+(.+?)(?:\s+(?:بال|بـ)\S+)?$",
    r"how (?:do (?:you|i)|to) say\s+(.+?)\s+in\s+\w+$", r"what (?:is|does) (.+?) (?:mean )?in (?:arabic|english)$",
    r"^(.+?)\s+(?:بالانجليزي|بالإنجليزي|بالانقليزي|بالعربي|in arabic|in english)$",
]


def _extract(question: str) -> str:
    text = re.sub(r"[؟?!.]+$", "", question.strip())
    for pattern in _PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1).strip(" «»\"'")
    return text


def _wikidata(term: str, src: str, dst: str) -> str | None:
    try:
        with httpx.Client(timeout=8, headers=HEADERS) as http:
            hits = http.get(API, params={"action": "wbsearchentities", "search": term, "language": src,
                                         "type": "item", "limit": 1, "format": "json"}).json().get("search", [])
            if not hits:
                return None
            qid = hits[0]["id"]
            labels = http.get(API, params={"action": "wbgetentities", "ids": qid, "props": "labels",
                                           "languages": dst, "format": "json"}).json()["entities"][qid]["labels"]
            return labels.get(dst, {}).get("value")
    except (httpx.HTTPError, ValueError, KeyError):
        return None


def translate(question: str) -> ToolResult:
    term = _extract(question)
    to_english = bool(re.search(r"[؀-ۿ]", term))
    ui_ar = bool(re.search(r"[؀-ۿ]", question))
    table = AR_TO_EN if to_english else EN_TO_AR
    key = _norm(term)
    result, source = table.get(key) or table.get(re.sub(r"^ال", "", key)), "dictionary"
    if not result and len(key.split()) > 1 and all(w in table for w in key.split()):
        result = " ".join(table[w] for w in key.split())   # word-by-word for simple known phrases
    if not result:
        result, source = _wikidata(term, "ar" if to_english else "en", "en" if to_english else "ar"), "wikidata"
    if not result:
        return ToolResult(False, f"ما لقيت ترجمة لـ «{term}»." if ui_ar else f"No translation found for «{term}».")
    target = ("الإنجليزية" if to_english else "العربية") if ui_ar else ("English" if to_english else "Arabic")
    text = f"🔤 **{term}** ← {target}: **{result}**" if ui_ar else f"🔤 **{term}** → {target}: **{result}**"
    if source == "wikidata":
        text += "\n\n🔗 https://www.wikidata.org"
    return ToolResult(True, text, entity=term)
