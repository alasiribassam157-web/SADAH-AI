"""Facts stated inside an Arabic request (services, phone, e-mail, city, opening hours, an event's date / time /
place). Nothing is invented: a fact that is not in the request stays absent and the template shows its placeholder.
Matching is done on the normalised text and sliced from the original, so values come back as the person typed them."""
import re
from dataclasses import dataclass, field

from builder.norm import n

WEEKDAYS = ("السبت", "الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة")
CITIES = ("الرياض", "جدة", "مكة", "المدينة", "الدمام", "الخبر", "الظهران", "الطائف", "تبوك", "أبها", "بريدة", "حائل", "جازان",
          "نجران", "الأحساء", "القصيم", "ينبع", "الجبيل", "دبي", "أبوظبي", "الشارقة", "الكويت", "الدوحة", "المنامة", "مسقط")
PLACES = ("قاعة", "فندق", "مطعم", "استراحة", "مزرعة", "منزل", "قصر", "جامعة", "مركز", "نادي", "حديقة", "ملعب", "مسرح", "مجمع")
TRIGGERS = {n(w) for w in ("خدماتنا", "خدمات", "نقدم", "نوفر", "يقدم", "تقدم", "مهاراتي", "مهارات", "نبيع", "منتجاتنا")}
STOP = {n(w) for w in ("لونه", "لون", "جوالي", "جوال", "رقم", "رقمي", "واتساب", "ايميل", "ايميلنا", "ايميلي", "بريدنا",
                      "نعمل", "دوامنا", "دوام", "في", "بتاريخ", "يوم", "الساعة", "من", "باسم", "فيه", "فيها", "عنواننا")}
_ALT = lambda words: "|".join(n(w) for w in words)  # noqa: E731
_HOUR = r"\d{1,2}(?::\d\d)?\s*(?:صباحا|الصبح|مساء|ليلا|ظهرا|عصرا|م|ص)?"
EMAIL = re.compile(r"[A-Za-z0-9._+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
PHONE = re.compile(r"(?<![\d+])(?:\+?(?:00)?9\d{2}\s?)?0?5\d{8}(?!\d)")
HOURS = re.compile(n(rf"من\s+(?:الساعة\s+)?{_HOUR}\s*(?:الى|حتى|لين)\s*(?:الساعة\s+)?{_HOUR}"))
TIME = re.compile(n(r"الساعة\s*(\d{1,2}(?::\d\d)?(?:\s*(?:صباحا|الصبح|مساء|ليلا|ظهرا|عصرا))?)"))
DATE = re.compile(r"(?:بتاريخ\s*)?(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)")
DAY = re.compile(n(rf"يوم\s+({_ALT(WEEKDAYS)})"))
PLACE = re.compile(n(rf"في\s+((?:{_ALT(PLACES)})(?:\s+[ء-ي]+){{0,2}})"))
CITY = re.compile(n(rf"(?:في|ب)\s*({_ALT(CITIES)})(?![ء-ي])"))


@dataclass
class Found:
    facts: dict = field(default_factory=dict)
    services: list = field(default_factory=list)
    text: str = ""   # the request without phone / e-mail / hours, so they never read as names or numbers


def _take(rx, nt: str, text: str, group: int = 0) -> tuple[str, str, str]:
    """Value (as typed) of the first match, plus both texts with the match blanked out."""
    m = rx.search(nt)
    if not m:
        return "", nt, text
    blank = lambda s: s[:m.start()] + " " * (m.end() - m.start()) + s[m.end():]  # noqa: E731
    return text[m.start(group):m.end(group)].strip(), blank(nt), blank(text)


def _services(text: str, skip: set) -> list[str]:
    toks, items, cur, on = text.split(), [], [], False
    for tok in toks:
        raw, nt = tok.strip("،,.:؛"), n(tok.strip("،,.:؛"))
        if not on:
            on = nt in TRIGGERS or (nt.startswith("و") and nt[1:] in TRIGGERS)
            continue
        base = nt[1:] if nt.startswith("و") and len(nt) > 3 else nt
        if nt in STOP or base in STOP or raw.isdigit():
            break
        if nt.startswith("و") and len(raw) > 3 and cur:   # «غسيل وتلميع»: a new item starts at a و-word
            items.append(" ".join(cur)); cur, raw = [], raw[1:]
        cur.append(raw)
        if tok[-1] in "،,":
            items.append(" ".join(cur)); cur = []
    items += [" ".join(cur)] if cur else []
    glued = lambda i: n(i) in skip or (n(i).startswith("و") and n(i)[1:] in skip)  # noqa: E731  «وتواصل»
    return [i for i in items if i and not glued(i) and len(i.split()) <= 4][:6]


def extract(text: str, skip: set = frozenset()) -> Found:
    """`skip` holds section words («تواصل», «أسعار»): «وفيه خدمات وتواصل» names sections, not services."""
    nt, facts = n(text), {}
    for key, rx, group in (("email", EMAIL, 0), ("phone", PHONE, 0), ("hours", HOURS, 0)):
        value, nt, text = _take(rx, nt, text, group)
        if value:
            facts[key] = " ".join(value.split())
    for key, rx in (("place", PLACE), ("time", TIME), ("date", DATE), ("city", CITY)):
        value, _, _ = _take(rx, nt, text, 1)
        if value:
            facts[key] = value
    if "date" not in facts and (m := DAY.search(nt)):
        facts["date"] = text[m.start(1):m.end(1)]
    if "city" in facts and "place" in facts and facts["city"] in facts["place"]:
        del facts["city"]   # «في فندق الريتز الرياض»: the city is part of the place
    return Found(facts, _services(text, skip), text)
