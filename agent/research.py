"""Wikipedia research: turn a natural question into a topic and return a short clean answer."""
import re

import httpx

from agent import kb

HEADERS = {"User-Agent": "NEXUS-1-Agent/1.0 (https://github.com/topics/nexus-1-ai) python-httpx"}
_DIACRITICS = re.compile(r"[ً-ْٰـ]")
_PREFIXES = re.compile(
    r"^(?:من فضلك|لو سمحت|please|can you|could you|nexus|"
    r"ابحث(?: في (?:الانترنت|الإنترنت|النت))? عن|ابحث|اعطني معلومات عن|أعطني معلومات عن|عطني معلومات عن|"
    r"ماذا تعرف عن|ماذا تعرفين عن|ما الذي تعرفه عن|وش تعرف عن|ايش تعرف عن|شو تعرف عن|شو بتعرف عن|"
    r"معلومات عن|قلي عن|قل لي عن|ابغى اعرف عن|ابي اعرف عن|"
    r"اخبرني عن|أخبرني عن|تكلم عن|حدثني عن|اشرح لي|اشرح|عرف|عرّف|وش هو|وش هي|ايش هو|ايش هي|"
    r"ما هو|ما هي|ماهو|ماهي|ما معنى|من هو|من هي|من هم|من كان|أين يقع|اين يقع|أين تقع|اين تقع|"
    r"أين|اين|متى|لماذا|ليش|كيف|شو هو|شو هي|شو يعني|ايه هو|ايه هي|يعني ايه|مين هو|مين هي|مين|فين|وين بيقع|وين|"
    r"امتى|ازاي|ليه|عايز اعرف عن|بدي اعرف عن|"
    r"search(?: the web)? for|find information about|information about|tell me about|tell me|"
    r"what do you know about|look up|research|google|explain|define|"
    r"what is|what are|what was|what's|who is|who was|who were|who are|where is|where was|"
    r"when did|when was|when is|why do|why does|why is|how does|how do|how is|how to|"
    r"the|a|an)\s+", re.IGNORECASE)
_SUFFIXES = re.compile(r"\s+(?:work|works|mean|means|بالتفصيل|باختصار|please|in short|briefly|in detail)$",
                       re.IGNORECASE)
_SHORT = re.compile(r"باختصار|بإختصار|in short|briefly|tl;?dr", re.IGNORECASE)
_LONG = re.compile(r"بالتفصيل|بالتفاصيل|اشرح اكثر|in detail|detailed|elaborate", re.IGNORECASE)


def answer_length(question: str) -> int:
    """Number of sentences: 1 for «باختصار», 8 for «بالتفصيل», otherwise 3."""
    return 1 if _SHORT.search(question) else 8 if _LONG.search(question) else 3


def to_topic(question: str) -> str:
    """'ما هو الذكاء الاصطناعي؟' -> 'الذكاء الاصطناعي';  'how does the internet work' -> 'internet'."""
    text = re.sub(r"[؟?!.]+", " ", question).strip()
    previous = None
    while previous != text:
        previous = text
        text = _SUFFIXES.sub("", _PREFIXES.sub("", text)).strip()
    return text or question.strip()


def _strip_al(topic: str) -> str:
    return " ".join(w[2:] if w.startswith("ال") and len(w) > 4 else w for w in topic.split())


def _query(http: httpx.Client, lang: str, params: dict, sentences: int = 3) -> dict | None:
    base = {"action": "query", "format": "json", "redirects": 1, "prop": "extracts|info|pageprops",
            "exintro": 1, "explaintext": 1, "exsentences": sentences, "inprop": "url"}
    pages = http.get(f"https://{lang}.wikipedia.org/w/api.php", params={**base, **params}).json()
    for page in (pages.get("query", {}).get("pages") or {}).values():
        if "missing" in page or "disambiguation" in page.get("pageprops", {}):
            continue
        if page.get("extract", "").strip():
            return page
    return None


def lookup(question: str, lang: str) -> tuple[str, str, str] | None:
    """Return (title, short answer, url) or None."""
    topic = to_topic(question)
    attempts = [{"titles": topic}]
    if lang == "ar":
        attempts.append({"titles": _strip_al(topic)})
    attempts.append({"generator": "search", "gsrsearch": topic, "gsrlimit": 1})
    if topic != question:
        attempts.append({"generator": "search", "gsrsearch": question, "gsrlimit": 1})
    sentences = answer_length(question)
    hit = kb.lookup(question, topic, lang, sentences)   # local knowledge library first
    if hit:
        return hit
    with httpx.Client(timeout=15, headers=HEADERS, follow_redirects=True) as http:
        page = next((p for params in attempts if (p := _query(http, lang, params, sentences))), None)
        if not page and lang == "ar":
            page = _english_fallback(http, topic, sentences)
        if page:
            text = _DIACRITICS.sub("", page["extract"])
            text = re.sub(r"\s*\([^()]*\)", "", text)   # drop pronunciation / date clutter
            text = re.sub(r"\s{2,}", " ", text).strip()
            return page["title"], text, page.get("fullurl", "")
    return None


def _english_fallback(http: httpx.Client, topic: str, sentences: int) -> dict | None:
    """No Arabic article: find the topic on Wikidata, then read its English Wikipedia article."""
    hits = http.get("https://www.wikidata.org/w/api.php", params={
        "action": "wbsearchentities", "search": topic, "language": "ar", "type": "item", "limit": 1,
        "format": "json"}).json().get("search", [])
    if not hits:
        return None
    entity = http.get("https://www.wikidata.org/w/api.php", params={
        "action": "wbgetentities", "ids": hits[0]["id"], "props": "sitelinks", "sitefilter": "enwiki",
        "format": "json"}).json()["entities"][hits[0]["id"]]
    title = entity.get("sitelinks", {}).get("enwiki", {}).get("title")
    if not title:
        return None
    page = _query(http, "en", {"titles": title}, sentences)
    if page:
        page["extract"] = "(من ويكيبيديا الإنجليزية) " + page["extract"]
    return page
