"""Direct factual answers from Wikidata (see facts_relations.py for the supported questions)."""
import re

import httpx

from agent.facts_relations import MULTI_VALUED, RELATIONS, UNITS

API = "https://www.wikidata.org/w/api.php"
HEADERS = {"User-Agent": "NEXUS-1-Agent/1.0 (https://github.com/topics/nexus-1-ai) python-httpx"}
AR_MONTHS = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر",
             "أكتوبر", "نوفمبر", "ديسمبر"]
EN_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
             "October", "November", "December"]


def _clean_entity(text: str) -> str:
    text = re.sub(r"[؟?!.،,]+$", "", text.strip())
    text = re.sub(r"\s+(?:باختصار|بالتفصيل|in short|in detail)$", "", text, flags=re.IGNORECASE)
    return re.sub(r"^(the|دولة|مدينة)\s+", "", text, flags=re.IGNORECASE).strip()


def _label(http: httpx.Client, qid: str, lang: str) -> str:
    data = http.get(API, params={"action": "wbgetentities", "ids": qid, "props": "labels",
                                 "languages": f"{lang}|en", "format": "json"}).json()
    labels = data["entities"][qid]["labels"]
    value = (labels.get(lang) or labels.get("en") or {"value": qid})["value"]
    return re.sub(r"[‎‏]", "", value)  # some Arabic labels carry invisible direction marks


def _best_claim(claims: list) -> dict | None:
    preferred = [c for c in claims if c.get("rank") == "preferred"]
    pool = preferred or [c for c in claims if c.get("rank") != "deprecated"]
    current = [c for c in pool if "P582" not in c.get("qualifiers", {})]  # skip claims that have an end date
    pool = current or pool
    if not pool:
        return None
    dated = [c for c in pool if "P585" in c.get("qualifiers", {})]
    if dated:  # figures with a date (population): the most recent one
        return max(dated, key=lambda c: c["qualifiers"]["P585"][0].get("datavalue", {}).get("value", {}).get("time", ""))
    return pool[0]  # otherwise the main value (France's currency is the euro, not the CFP franc)


def _quantity(value: dict, claim: dict, lang: str) -> tuple[str, str]:
    amount = float(value["value"]["amount"])
    shown = f"{amount:,.0f}" if amount.is_integer() or amount > 1000 else f"{amount:,.2f}"
    unit = UNITS.get(value["value"].get("unit", "").rsplit("/", 1)[-1])
    if unit:
        shown += " " + (unit[0] if lang == "ar" else unit[1])
    when = claim.get("qualifiers", {}).get("P585", [{}])[0].get("datavalue", {}).get("value", {})
    year = when.get("time", "")[1:5]
    return shown, (f" ({year})" if year else "")


def _format(value: dict, claim: dict, http: httpx.Client, lang: str) -> tuple[str, str]:
    kind = value["type"]
    if kind == "wikibase-entityid":
        return _label(http, value["value"]["id"], lang), ""
    if kind == "quantity":
        return _quantity(value, claim, lang)
    if kind == "time":
        y, m, d = (int(x) for x in re.match(r"[+-](\d+)-(\d+)-(\d+)", value["value"]["time"]).groups())
        months = AR_MONTHS if lang == "ar" else EN_MONTHS
        if m and d:
            return (f"{d} {months[m - 1]} {y}" if lang == "ar" else f"{months[m - 1]} {d}, {y}"), ""
        return str(y), ""
    return str(value["value"]), ""


def match_relation(question: str) -> tuple[str, str, str, str] | None:
    """(property, subject, Arabic template, English template) for a supported question, else None."""
    # Common spelling: a final «ه» written for «ة» (عاصمه، مكه) should still match the patterns.
    if re.search(r"(?:عاصمه|مساحه|عمله|اللغه)", question):
        question = re.sub(r"(?<=\w)ه\b", "ة", question)
    for prop, pattern, tpl_ar, tpl_en in RELATIONS:
        m = re.search(pattern, question, re.IGNORECASE)
        if m:
            return prop, _clean_entity(next(g for g in m.groups() if g)), tpl_ar, tpl_en
    return None


def fact_details(question: str, lang: str) -> dict | None:
    """Like answer_fact, plus the raw value and its kind so another agent can cross-check it."""
    rel = match_relation(question)
    if not rel:
        return None
    prop, entity, tpl_ar, tpl_en = rel
    for _attempt in range(2):  # one retry: Wikidata sometimes answers slowly
        try:
            return _lookup(prop, entity, tpl_ar if lang == "ar" else tpl_en, lang)
        except httpx.TimeoutException:
            continue
        except (httpx.HTTPError, KeyError, ValueError, StopIteration, AttributeError):
            return None
    return None


def answer_fact(question: str, lang: str) -> tuple[str, str, str] | None:
    """Return (answer markdown, source url, entity name) or None if not a known relation."""
    d = fact_details(question, lang)
    return (d["answer"], d["url"], d["name"]) if d else None


def numeric_fact(entity: str, prop: str, lang: str) -> tuple[str, float, str, str] | None:
    """(name, number, unit, source url) for quantities such as population (P1082) or area (P2046)."""
    with httpx.Client(timeout=12, headers=HEADERS) as http:
        hits = http.get(API, params={"action": "wbsearchentities", "search": _clean_entity(entity), "language": lang,
                                     "uselang": lang, "type": "item", "limit": 3, "format": "json"}).json()
        for hit in hits.get("search", []):
            claims = http.get(API, params={"action": "wbgetentities", "ids": hit["id"], "props": "claims",
                                           "format": "json"}).json()["entities"][hit["id"]]["claims"]
            found = next((p for p in prop.split("|") if _best_claim(claims.get(p, []))), None)
            claim = _best_claim(claims.get(found, [])) if found else None
            value = claim and claim["mainsnak"].get("datavalue", {}).get("value")
            if isinstance(value, dict) and "amount" in value:
                unit = UNITS.get(value.get("unit", "").rsplit("/", 1)[-1], ("", ""))[0 if lang == "ar" else 1]
                return _label(http, hit["id"], lang), float(value["amount"]), unit, f"https://www.wikidata.org/wiki/{hit['id']}"
    return None


def _lookup(prop: str, entity: str, tpl: str, lang: str) -> dict | None:
    with httpx.Client(timeout=10, headers=HEADERS) as http:
        hits = http.get(API, params={"action": "wbsearchentities", "search": entity, "language": lang,
                                     "uselang": lang, "type": "item", "limit": 3, "format": "json"}).json()
        for hit in hits.get("search", []):
            qid = hit["id"]
            claims = http.get(API, params={"action": "wbgetentities", "ids": qid, "props": "claims",
                                           "format": "json"}).json()["entities"][qid]["claims"]
            found = next((p for p in prop.split("|") if _best_claim(claims.get(p, []))), None)
            claim = _best_claim(claims.get(found, [])) if found else None
            if not claim or "datavalue" not in claim["mainsnak"]:
                continue
            value, detail = _format(claim["mainsnak"]["datavalue"], claim, http, lang)
            if found in MULTI_VALUED:
                values = [c for c in claims[found] if c.get("rank") != "deprecated" and "datavalue" in c["mainsnak"]][:3]
                value = ("، " if lang == "ar" else ", ").join(
                    _format(c["mainsnak"]["datavalue"], c, http, lang)[0] for c in values)
            name = _label(http, qid, lang)
            raw = claim["mainsnak"]["datavalue"]
            amount = raw["value"].get("amount") if raw["type"] == "quantity" else None
            return {"answer": tpl.format(e=name, v=value, d=detail), "url": f"https://www.wikidata.org/wiki/{qid}",
                    "name": name, "value": value, "kind": raw["type"], "amount": amount, "prop": found}
    return None
