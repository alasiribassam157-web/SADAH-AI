"""«ما هي أفلام جوني ديب؟»: the real list of works of a person from Wikidata, not the first sentences of an article.

films / series → cast member (P161) · songs → performer (P175) · books / novels → author (P50).
The person is found with wbsearchentities, the works with one SPARQL query (labels in Arabic, else English).
"""
import re

import httpx

from agent.research import HEADERS

SPARQL = "https://query.wikidata.org/sparql"
API = "https://www.wikidata.org/w/api.php"
# kind -> (words, the kind of work, property linking person → work, Arabic title, English title)
KINDS = [("film", r"افلام|أفلام|فيلم|movies?|films?|filmography", "Q11424", "P161", "أفلام", "Films"),
         ("series", r"مسلسلات|series|tv shows?", "Q5398426", "P161", "مسلسلات", "TV series"),
         ("song", r"اغاني|أغاني|songs?", "Q7366", "P175", "أغاني", "Songs"),
         ("book", r"روايات|مؤلفات|كتب|novels?|books?", "Q7725634", "P50", "مؤلفات", "Books")]
_TITLE = re.compile(r"^(?:ما|ماهي|ماهو|وش|ايش|شو|اذكر|اعطني|عطني|هات|قائمة|list|what|show me|give me)\s*(?:هي|هو|are|is|of)?\s*"
                    r"(?:all\s+|the\s+)?", re.I)
_ROLE = re.compile(r"^(?:الممثل|الممثلة|الفنان|الفنانة|المغني|المغنية|الكاتب|الكاتبة|المخرج|للممثل|للكاتب|للمغني|ل)\s+")
_EN_OF = re.compile(r"(?:of|by|with|starring|from)\s+(.+)$", re.I)


def parse(question: str) -> tuple[tuple, str] | None:
    """((kind row), person name) when the question asks for the works of someone, else None."""
    text = re.sub(r"[؟?!.]+", " ", question).strip()
    for row in KINDS:
        m = re.search(rf"(?<!\w)(?:{row[1]})(?!\w)", text, re.I)
        if not m:
            continue
        after, before = text[m.end():].strip(), text[:m.start()].strip()
        arabic = bool(re.search(r"[؀-ۿ]", text))
        name = _ROLE.sub("", after).strip() if arabic and not _TITLE.sub("", before) else ""
        if not name and (en := _EN_OF.search(after)):
            name = en.group(1).strip()
        if not name and not arabic:
            name = _TITLE.sub("", before).strip()
        if not arabic and not name[:1].isupper():   # «best books» is not a person
            name = ""
        if re.match(r"(?:بال|في\s|in\s)", name):         # «book بالعربي»: a translation, not a person
            name = ""
        name = re.sub(r"\s+(?:كلها|كلهم|كامله|كاملة|all|list)$", "", name, flags=re.I)
        if 2 <= len(name) <= 40 and len(name.split()) <= 4:
            return row, name
    return None


def is_works(question: str) -> bool:
    return parse(question) is not None


def _person(http: httpx.Client, name: str, lang: str) -> tuple[str, str] | None:
    """The first search hit that is a human (one search per language, one SPARQL check for all hits)."""
    hits = []
    for language in dict.fromkeys([lang, "en"]):
        hits += http.get(API, params={"action": "wbsearchentities", "search": name, "language": language,
                                      "type": "item", "limit": 5, "format": "json"}).json().get("search", [])
    ids = list(dict.fromkeys(h["id"] for h in hits))
    if not ids:
        return None
    query = "SELECT ?i WHERE { VALUES ?i { " + " ".join(f"wd:{i}" for i in ids) + " } ?i wdt:P31 wd:Q5 }"
    humans = {r["i"]["value"].rsplit("/", 1)[-1] for r in
              http.get(SPARQL, params={"query": query, "format": "json"}).json()["results"]["bindings"]}
    label = {h["id"]: h.get("label", name) for h in hits}
    return next(((i, label[i]) for i in ids if i in humans), None)


def fetch(person: str, row: tuple, lang: str, http: httpx.Client) -> list[tuple[str, int]]:
    _, _, kind, prop, _, _ = row
    query = (f'SELECT ?w ?wLabel (MIN(YEAR(?d)) AS ?y) WHERE {{ ?w wdt:{prop} wd:{person}; wdt:P31/wdt:P279* wd:{kind}. '
             f'OPTIONAL {{ ?w wdt:P577 ?d }} SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{lang},en". }} }} '
             f'GROUP BY ?w ?wLabel ORDER BY ?y LIMIT 80')
    rows = http.get(SPARQL, params={"query": query, "format": "json"}).json()["results"]["bindings"]
    out, seen = [], set()
    for r in rows:
        label = r["wLabel"]["value"]
        if re.fullmatch(r"Q\d+", label) or label in seen:   # an item with no label in any language
            continue
        seen.add(label)
        out.append((label, int(r["y"]["value"]) if "y" in r else 0))
    return out


def works(question: str, lang: str, http: httpx.Client | None = None) -> dict | None:
    """{"answer", "url", "name", "count"} — None when the question is not about works or the person is unknown."""
    parsed = parse(question)
    if not parsed:
        return None
    row, name = parsed
    with (http or httpx.Client(timeout=12, headers=HEADERS, follow_redirects=True)) as client:
        who = _person(client, name, lang)
        if not who:
            return None
        items = fetch(who[0], row, lang, client)
    ar = lang == "ar"
    head = row[4] if ar else row[5]
    if not items:
        return {"answer": "", "url": f"https://www.wikidata.org/wiki/{who[0]}", "name": who[1], "count": 0}
    lines = [f"• {t}" + (f" ({y})" if y else "") for t, y in items[:30]]
    more = (f"\n… و{len(items) - 30} أخرى" if ar else f"\n… and {len(items) - 30} more") if len(items) > 30 else ""
    title = f"**{head} {who[1]}** ({len(items)}):" if ar else f"**{head} — {who[1]}** ({len(items)}):"
    return {"answer": title + "\n\n" + "\n".join(lines) + more, "url": f"https://www.wikidata.org/wiki/{who[0]}",
            "name": who[1], "count": len(items)}
