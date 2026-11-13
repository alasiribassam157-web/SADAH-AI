"""Do two independent sources say the same thing?  Pure functions, no network (tested offline).

verified = a second source states the same value · single = nobody else confirms or denies it
conflict = a second source clearly states a different value for the same thing.
"""
import re

VERIFIED, SINGLE, CONFLICT = "verified", "single", "conflict"
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_SCALE = [(r"مليار|billion", 1e9), (r"مليون|ملايين|million", 1e6), (r"ألف|الف|آلاف|الاف|thousand", 1e3)]
_NUMBER = re.compile(r"(\d(?:[\d,٬.٫]*\d)?)\s*(مليار|مليون|ملايين|ألف|الف|آلاف|الاف|billion|million|thousand)?",
                     re.IGNORECASE)
# words that sit next to the number in a sentence about this property
KEYWORDS = {"P1082": r"سكان|نسمة|نسمه|population|inhabitants|people",
            "P2046": r"مساح|كم²|كم2|كيلومتر مربع|km2|km²|square",
            "P2048": r"ارتفاع|طول|متر|height|tall|metres|meters", "P2044": r"ارتفاع|متر|elevation|metres|meters"}
TOLERANCE = 0.05   # figures from different years differ a little (population 2020 vs 2023)


def numbers(text: str) -> list[tuple[float, int]]:
    """Every number in the text with its scale applied, and where it starts: «125.7 مليون» -> 125700000."""
    out = []
    for m in _NUMBER.finditer(text.translate(_DIGITS)):
        value = _parse(m.group(1).replace("٬", ",").replace("٫", "."))
        if value is None:
            continue
        word = (m.group(2) or "").lower()
        scale = next((f for pat, f in _SCALE if word and re.fullmatch(pat, word)), 1)
        value *= scale if value < 1000 else 1   # «7.009.120 مليون» is already the full figure
        out.append((value, m.start()))
    return out


def _parse(raw: str) -> float | None:
    """«1,010,408» «7.009.120» (dots as thousands) «4,67» (comma as decimal) «125.7»."""
    if re.fullmatch(r"\d{1,3}(?:\.\d{3}){2,}", raw):
        raw = raw.replace(".", "")
    elif re.fullmatch(r"\d+,\d{1,2}", raw):
        raw = raw.replace(",", ".")
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def norm(text: str) -> list[str]:
    """Words without diacritics, «ال» or letter variants, so «الرياض» matches «رياض»."""
    text = re.sub(r"[ً-ْٰـ()\[\]]", "", text.lower()).translate(str.maketrans("أإآىة", "اااىه"))
    words = []
    for w in re.findall(r"\w+", text):
        for p in ("وال", "بال", "لل", "ال"):
            if w.startswith(p) and len(w) - len(p) >= 2:
                w = w[len(p):]
                break
        words.append(w)
    return words


def _agree(a: float, b: float) -> bool:
    return a > 0 and abs(a - b) / a <= TOLERANCE


def compare_number(value: float, text: str, prop: str = "") -> tuple[str, str]:
    found = numbers(text)
    hit = next((n for n, _ in found if _agree(value, n)), None)
    if hit is not None:
        return VERIFIED, f"{hit:,.0f}"
    key = KEYWORDS.get(prop)
    if key:  # a different figure right next to the property's words = a real disagreement
        spots = [m.start() for m in re.finditer(key, text, re.IGNORECASE)]
        for n, pos in found:
            if 0.5 <= n / value <= 2 and any(abs(pos - s) <= 60 for s in spots):
                return CONFLICT, f"{n:,.0f}"
    return SINGLE, ""


def compare_text(value: str, text: str) -> tuple[str, str]:
    """A name (capital, currency, founder): every word of it must appear in the other source."""
    first = re.split(r"[،,]", value)[0]
    wanted = [w for w in norm(first) if len(w) > 1]
    have = set(norm(text))
    have |= {h[1:] for h in have if h[:1] in "وبلفك" and len(h) > 3}   # «وطوكيو» / «بطوكيو»
    if wanted and all(w in have for w in wanted):
        return VERIFIED, first.strip()
    return SINGLE, ""


def compare_date(value: str, text: str) -> tuple[str, str]:
    year = re.search(r"\d{3,4}", value.translate(_DIGITS))
    if year and re.search(rf"(?<!\d){year.group()}(?!\d)", text.translate(_DIGITS)):
        return VERIFIED, year.group()
    return SINGLE, ""


def judge(fact: dict, text: str) -> tuple[str, str]:
    """Compare a Wikidata fact (facts.fact_details) with another source's text."""
    if not text:
        return SINGLE, ""
    value = re.sub(r"\*", "", str(fact.get("value", "")))
    if fact.get("kind") == "quantity" and fact.get("amount") is not None:
        return compare_number(abs(float(fact["amount"])), text, (fact.get("prop") or "").split("|")[0])
    if fact.get("kind") == "time":
        return compare_date(value, text)
    if fact.get("kind") in ("wikibase-entityid", "string", "monolingualtext"):
        return compare_text(value, text)
    return SINGLE, ""
