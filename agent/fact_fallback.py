"""Silent fallback when Wikidata is rate-limited or silent: read the fact out of Wikipedia's introduction
or the local knowledge base with regular expressions, so a fact question is never answered with «لا جواب».

`rescue()` returns the same dict shape as `facts.fact_details` with source="fallback"; the critic does not
call such an answer «verified by two sources», because both texts descend from Wikipedia.
"""
import re

import httpx

from agents.consensus import KEYWORDS, numbers
from agent.core_facts import norm
from agent.facts_relations import UNITS

_STOP = r"(?:و|التي|الذي|وهي|وأكبر|ويبلغ|وتقع|وتعد|which|and|with|,|\.)"
_NAME = r"([^\s،.,()؛]+(?:\s(?!{s}\b)[^\s،.,()؛]+)?)".format(s=_STOP)
_PAT = {
    "P36": (rf"عاصمت(?:ها|ه)\s+(?:هي\s+)?(?:مدينة\s+)?{_NAME}", r"capital(?: city)?\s+(?:is|being)\s+(?:the city of\s+)?([A-Z][\w'\-]+(?:\s[A-Z][\w'\-]+)?)"),
    "P38": (rf"عملت(?:ها|ه)\s+(?:الرسمية\s+)?(?:هي\s+)?{_NAME}", r"currency\s+is\s+the\s+([\w\- ]+?)(?:\s*[(,.;]|\s+and\b)"),
    "P37": (rf"لغت(?:ها|ه)\s+الرسمية\s+(?:هي\s+)?{_NAME}", r"official language[s]?\s+(?:is|are)\s+([A-Z]\w+)"),
    "P30": (r"(?:تقع|يقع)\s+(?:في\s+)?(?:قارة\s+)?(آسيا|أفريقيا|إفريقيا|أوروبا|أمريكا الشمالية|أمريكا الجنوبية|أوقيانوسيا)",
            r"(?:in|of)\s+(Asia|Africa|Europe|North America|South America|Oceania)\b"),
}
_YEAR = {"P571": (r"(?:تأسس\w*|أسس\w*|قامت|نشأت|تأسيس\w*)", r"(?:founded|established|created)"),
         "P569": (r"(?:ولد|وُلد|مولود)", r"born")}
_WHERE = r"(?:ولد|وُلد)\s+(?:في\s+)?(?:مدينة\s+)?{n}|born\s+(?:in|at)\s+(?:the city of\s+)?([A-Z][\w'\-]+)".format(n=_NAME)


def _number(prop: str, text: str, low: float) -> float | None:
    words = KEYWORDS.get(prop.split("|")[0], "")
    spots = [m.start() for m in re.finditer(words, text, re.I)] if words else []
    near = [(min((abs(pos - s) for s in spots), default=99), value) for value, pos in numbers(text) if value >= low]
    near = [n for n in near if n[0] <= 60]
    return min(near)[1] if near else None


def extract(prop: str, text: str, lang: str) -> tuple[str, float | None, str] | None:
    """(value text, number, kind) read from `text`, or None."""
    key, i = prop.split("|")[0], 0 if lang == "ar" else 1
    if key in ("P1082", "P2046", "P2048", "P2044"):
        n = _number(key, text, 1000 if key == "P1082" else 1)
        unit = {"P2046": "Q712226", "P2048": "Q11573", "P2044": "Q11573"}.get(key)
        sym = UNITS[unit][i] if unit else ""
        return (f"{n:,.0f}" + (f" {sym}" if sym else ""), n, "quantity") if n else None
    if key in _YEAR:
        m = re.search(rf"{_YEAR[key][i]}[^.\n]{{0,80}}?(?<!\d)(\d{{3,4}})(?!\d)", text, re.I)
        return (m.group(1), None, "time") if m else None
    pattern = _WHERE.split("|")[i] if key == "P19" else _PAT.get(key, ("", ""))[i]
    m = re.search(pattern, text, re.I) if pattern else None
    return (m.group(1).strip(), None, "wikibase-entityid") if m else None


def _texts(entity: str, lang: str):
    """Candidate source texts, best first: Wikipedia's introduction, then local knowledge-base passages."""
    try:
        from agent.research import intro
        page = intro(entity, lang, timeout=4)
        if page:
            yield page[2], page[0], page[1]
    except (httpx.HTTPError, KeyError, ValueError):
        pass
    try:
        from agent.local_kb_agent import LocalKBAgent
        for p in LocalKBAgent().passages(entity, lang, 4):
            if norm(entity) in norm(p["title"]):
                yield p["url"], p["title"], p["text"]
    except Exception:  # noqa: BLE001 - the fallback must never raise
        return


def rescue(prop: str, entity: str, tpl: str, lang: str) -> dict | None:
    """Answer from Wikipedia / the local knowledge base when Wikidata cannot."""
    for url, title, text in _texts(entity, lang):
        got = extract(prop, text, lang)
        if got:
            value, amount, kind = got
            return {"answer": tpl.format(e=title, v=value, d=""), "url": url or "https://wikipedia.org", "name": title,
                    "value": value, "kind": kind, "amount": amount, "prop": prop.split("|")[0], "source": "fallback"}
    return None
