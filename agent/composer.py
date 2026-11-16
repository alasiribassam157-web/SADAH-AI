"""Multi-step reasoning (SADAH v5): comparisons («قارن بين سكان مصر والسعودية») and compound questions
(«ما هي عاصمة اليابان وكم عدد سكانها») answered by chaining several lookups."""
import re

import httpx

from agent.facts import numeric_fact
from agent.tools import ToolResult

# property words -> (Wikidata property, Arabic label, English label)
PROPERTIES = [
    (r"سكان|سكانا|سكاناً|population|populous|people", "P1082", "عدد السكان", "population"),
    (r"مساحة|مساحه|اكبر|أكبر|bigger|larger|area", "P2046", "المساحة", "area"),
    (r"ارتفاع|اطول|أطول|أعلى|اعلى|طول|taller|higher|height|tall", "P2048|P2044", "الارتفاع", "height"),
]
_PAIR = [
    r"قارن بين\s+(?:\S+\s+)?(.+?)\s+و\s*(.+?)(?:\s+في\s+.+)?$",
    r"(?:ايهما|أيهما|مين|من|وش|ايش)\s+(?:\S+\s+){1,2}?(.+?)\s+(?:ام|أم|او|أو|ولا)\s+(.+)$",
    r"compare\s+(?:the\s+)?(?:\w+\s+of\s+)?(.+?)\s+(?:and|vs\.?|versus|with)\s+(.+)$",
    r"which (?:is|has)\s+(?:\w+\s+){1,3}?(.+?)\s+or\s+(.+)$",
]
_FOLLOW = re.compile(r"\s+(و(?:كم|ما|ماذا|من|متى|أين|اين|وش|ايش|هل)\b.*)$|\s+(and (?:what|how|who|when|where|which)\b.*)$",
                     re.IGNORECASE)


def is_comparison(question: str) -> bool:
    return bool(re.search(r"قارن|مقارنة|ايهما|أيهما|compare|which is (?:bigger|larger|taller|more)|"
                          r"which has more|(?:اكبر|أكبر|اطول|أطول).+(?:ام|أم|ولا)\s", question, re.IGNORECASE))


def split_compound(question: str) -> list[str]:
    """«ما هي عاصمة اليابان وكم عدد سكانها» -> [«ما هي عاصمة اليابان», «وكم عدد سكانها»] (pronouns resolved later)."""
    if is_comparison(question):
        return [question]
    m = _FOLLOW.search(question.strip())
    if not m or len(question.split()) < 5:
        return [question]
    second = (m.group(1) or m.group(2)).strip()
    return [question[:m.start()].strip(), second]


def compare(question: str) -> ToolResult:
    ar = bool(re.search(r"[؀-ۿ]", question))
    text = re.sub(r"[؟?!.]+$", "", question.strip())
    prop, label_ar, label_en = next(((p, a, e) for pat, p, a, e in PROPERTIES if re.search(pat, text, re.IGNORECASE)),
                                    PROPERTIES[0][1:])
    pair = next((m.groups() for p in _PAIR if (m := re.search(p, text, re.IGNORECASE))), None)
    if not pair:
        return ToolResult(False, "اكتب الشيئين اللي تبي تقارن بينهم، مثلاً: قارن بين سكان مصر والسعودية" if ar
                          else "Name the two things, e.g. compare the population of Egypt and Saudi Arabia")
    cleaner = r"^(?:عدد\s+)?(?:سكان|مساحة|ارتفاع|طول)\s+|^(?:the\s+)?(?:population|area|height)\s+of\s+"
    entities = [re.sub(cleaner, "", e.strip(), flags=re.IGNORECASE).strip() for e in pair]
    try:
        facts = [numeric_fact(e, prop, "ar" if ar else "en") for e in entities]
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        return ToolResult(False, f"تعذّر جلب البيانات: {exc}" if ar else f"Data service error: {exc}")
    if not all(facts):
        missing = entities[facts.index(None)]
        return ToolResult(False, f"ما لقيت {label_ar} لـ «{missing}»." if ar else f"No {label_en} found for «{missing}».")
    (n1, v1, unit, url1), (n2, v2, _, url2) = facts
    big, small = ((n1, v1), (n2, v2)) if v1 >= v2 else ((n2, v2), (n1, v1))
    fmt = (lambda v: f"{v:,.0f} {unit}".strip())
    ratio = big[1] / small[1] if small[1] else 0
    if ar:
        verdict = f"**{big[0]}** أكبر بـ **{fmt(big[1] - small[1])}**" + (f" (حوالي {ratio:.1f} ضعف)" if ratio >= 1.15 else "")
        body = f"⚖️ **مقارنة {label_ar}**\n• {n1}: **{fmt(v1)}**\n• {n2}: **{fmt(v2)}**\n\n{verdict}"
    else:
        verdict = f"**{big[0]}** is larger by **{fmt(big[1] - small[1])}**" + (f" (about {ratio:.1f}×)" if ratio >= 1.15 else "")
        body = f"⚖️ **{label_en.title()} comparison**\n• {n1}: **{fmt(v1)}**\n• {n2}: **{fmt(v2)}**\n\n{verdict}"
    return ToolResult(True, f"{body}\n\n🔗 {url1}", entity=big[0])
