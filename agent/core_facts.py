"""Pre-baked core facts: capital, currency, continent, language, area, population, founding and a few famous entities.

`lookup()` answers from `data/kb/facts_cache.json` in well under a millisecond with no network, so the most
asked questions never depend on Wikidata's rate limit.  The answer has the same shape as `facts.fact_details`
(answer, url, name, value, kind, amount, prop) and is still cross-checked against Wikipedia by the critic.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

from agent.facts_relations import UNITS

PATH = Path(__file__).resolve().parent.parent / "data" / "kb" / "facts_cache.json"
_MARKS = re.compile(r"[ً-ْٰـ]")
_FILLER = re.compile(r"^(?:دولة|جمهورية|مملكة|سلطنة|مدينة|شركة|the|state of|kingdom of|republic of)\s+", re.I)
_TEXT = {"P36", "P38", "P30", "P37", "P19", "P112"}       # values that are names
_TIME = {"P571", "P569"}
_NUMBER = {"P1082", "P2046", "P2048"}
_UNIT = {"P2046": "Q712226", "P2048": "Q11573"}


def norm(text: str) -> str:
    """One spelling for matching: no diacritics, no «ال», أ/إ/آ→ا, ة→ه, ى→ي, lower case."""
    text = _FILLER.sub("", _MARKS.sub("", text.strip().strip("؟?!.،, ")).lower())
    text = re.sub(r"[أإآ]", "ا", text).replace("ة", "ه").replace("ى", "ي")
    return re.sub(r"\bال(?=\S{2})", "", text)


@lru_cache(maxsize=1)
def _index() -> dict:
    try:
        data = json.loads(PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    out = {}
    for rec in data.get("countries", []) + data.get("entities", []):
        for name in [rec["ar"], rec["en"], *rec.get("alias", [])]:
            out.setdefault(norm(name), rec)
    return out


def known(entity: str) -> bool:
    return norm(entity) in _index()


def _show(prop: str, raw, lang: str) -> tuple[str, float | None, str]:
    """(text, number or None, kind) for one cached value."""
    i = 0 if lang == "ar" else 1
    if prop in _NUMBER:
        amount = float(raw[0] if isinstance(raw, list) else raw)
        unit = UNITS.get(_UNIT.get(prop, ""), ("", ""))[i]
        return f"{amount:,.0f}" + (f" {unit}" if unit else ""), amount, "quantity"
    if prop in _TIME:
        return (raw if isinstance(raw, str) else raw[i]), None, "time"
    return raw[i], None, "wikibase-entityid" if prop in _TEXT and prop != "P112" else "string"


def lookup(prop: str, entity: str, tpl: str, lang: str) -> dict | None:
    """The cached fact for (property, entity) formatted with the relation's template, or None."""
    rec = _index().get(norm(entity))
    key = next((p for p in prop.split("|") if rec and rec.get(p) not in (None, "")), None)
    if not key:
        return None
    raw = rec[key]
    if key == "P2048":
        raw = raw[0]
    text, amount, kind = _show(key, raw, lang)
    name = rec["ar"] if lang == "ar" else rec["en"]
    url = f"https://{lang}.wikipedia.org/wiki/{name.replace(' ', '_')}"
    return {"answer": tpl.format(e=name, v=text, d=""), "url": url, "name": name, "value": text, "kind": kind,
            "amount": amount, "prop": key, "source": "cache"}


def number(entity: str, prop: str, lang: str) -> tuple[str, float, str, str] | None:
    """(name, value, unit, url) for a cached quantity: the shield for comparisons («أكبر: مصر أم السعودية»)."""
    d = lookup(prop, entity, "{v}", lang)
    if not d or d["amount"] is None:
        return None
    unit = UNITS.get(_UNIT.get(d["prop"], ""), ("", ""))[0 if lang == "ar" else 1]
    return d["name"], d["amount"], unit, d["url"]
