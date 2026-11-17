"""Date reasoning (SADAH v5): days until events (Ramadan, Eid, national days), ages, gaps between dates,
dates N days from now, and the weekday of any date. Hijri dates come from api.aladhan.com."""
import re
from datetime import date, datetime, timedelta

import httpx

from agent.live_skills import AR_DAYS, AR_MONTHS, HEADERS, TZ
from agent.tools import ToolResult

EN_MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
             "november", "december"]
_AR_MONTH_ALIASES = {**{m: i + 1 for i, m in enumerate(AR_MONTHS)}, "ابريل": 4, "اغسطس": 8, "اكتوبر": 10, "مايو": 5}
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
# event -> (hijri month, hijri day) or (None, gregorian (month, day))
EVENTS = {"رمضان": (9, 1), "ramadan": (9, 1), "عيد الفطر": (10, 1), "eid al-fitr": (10, 1), "eid al fitr": (10, 1),
          "عيد الأضحى": (12, 10), "عيد الاضحى": (12, 10), "eid al-adha": (12, 10), "eid al adha": (12, 10),
          "يوم عرفة": (12, 9), "رأس السنة الهجرية": (1, 1), "راس السنة الهجرية": (1, 1),
          "اليوم الوطني": (None, (9, 23)), "national day": (None, (9, 23)), "يوم التأسيس": (None, (2, 22)),
          "founding day": (None, (2, 22)), "رأس السنة": (None, (1, 1)), "راس السنة": (None, (1, 1)),
          "new year": (None, (1, 1))}
_NAMES = {"رمضان": "رمضان", "ramadan": "Ramadan", "عيد الفطر": "عيد الفطر", "عيد الأضحى": "عيد الأضحى",
          "عيد الاضحى": "عيد الأضحى", "يوم عرفة": "يوم عرفة"}


_AGE_WORDS = re.compile(r"عمري|مواليد|انولدت|ولدت|how old am i|born in")
_ASKING = re.compile(r"(?<!\w)(?:كم|احسب|كيف|how|what|calculate)(?!\w)|\?|؟")


def asks_age_from_date(q: str) -> bool:
    """An age question date_math can compute: it has a full date or a birth year (1900…today) AND asks.
    «عمري 21 سنه» is a statement, and «كم عمري» has nothing to compute from — both belong to the companion."""
    q = q.translate(_DIGITS)
    has_date = bool(_dates(q)) or any(1900 <= int(n) <= datetime.now().year for n in re.findall(r"(?<!\d)\d{4}(?!\d)", q))
    return bool(_AGE_WORDS.search(q)) and has_date and bool(_ASKING.search(q))


def handles(question: str) -> bool:
    q = question.lower()
    return asks_age_from_date(q) or bool(re.search(
        r"كم باقي|كم بقي|كم يوم (?:باقي|بقي|بين|على|لين|حتى)|متى رمضان|متى العيد|"
        r"days until|how many days (?:until|till|left|between)|"
        r"بين .* و .*\d|بعد \d+ (?:يوم|أيام|ايام)|\d+ days from|from now|"
        r"(?:اي|أي|وش) يوم (?:يوافق|كان|بيكون)|what day (?:is|was|will)", q)) or any(e in q for e in EVENTS)


def mentions_event(question: str) -> bool:
    return any(e in question.lower() for e in EVENTS)


def _dates(text: str) -> list[date]:
    text = text.translate(_DIGITS).lower()
    found = []
    for y, m, d in re.findall(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", text):
        found.append(date(int(y), int(m), int(d)))
    for d, m, y in re.findall(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", text):
        found.append(date(int(y), int(m), int(d)))
    for d, name, y in re.findall(r"(\d{1,2})\s+([a-z؀-ۿ]+)\s+(\d{4})", text):
        month = _AR_MONTH_ALIASES.get(name) or (EN_MONTHS.index(name) + 1 if name in EN_MONTHS else None)
        if month:
            found.append(date(int(y), month, int(d)))
    return found


def _hijri_event(month: int, day: int, today: date) -> date:
    with httpx.Client(timeout=10, headers=HEADERS, follow_redirects=True) as http:
        year = int(http.get(f"https://api.aladhan.com/v1/gToH/{today:%d-%m-%Y}").json()["data"]["hijri"]["year"])
        for y in (year, year + 1):
            g = http.get(f"https://api.aladhan.com/v1/hToG/{day:02d}-{month:02d}-{y}").json()["data"]["gregorian"]["date"]
            event = datetime.strptime(g, "%d-%m-%Y").date()
            if event >= today:
                return event
    raise ValueError("event not found")


def _fmt(d: date, ar: bool) -> str:
    return f"{AR_DAYS[d.weekday()]} {d.day} {AR_MONTHS[d.month - 1]} {d.year}" if ar else d.strftime("%A, %B %d, %Y")


def answer(question: str) -> ToolResult:
    ar, q = bool(re.search(r"[؀-ۿ]", question)), question.lower().translate(_DIGITS)
    today = datetime.now(TZ).date()
    try:
        event = next((e for e in sorted(EVENTS, key=len, reverse=True) if e in q), None)
        if event:
            hm, gd = EVENTS[event]
            target = _hijri_event(hm, gd, today) if hm else date(today.year + (date(today.year, *gd) < today), *gd)
            days, name = (target - today).days, _NAMES.get(event, event)
            text = (f"باقي على {name} **{days} يوم**، ويوافق {_fmt(target, ar)}" if ar else
                    f"**{days} days** until {name.title()} — {_fmt(target, ar)}")
            return ToolResult(True, ("🎉 " if days == 0 else "📅 ") + text)
        dates, nums = _dates(question), [int(n) for n in re.findall(r"\b\d+\b", q)]
        if re.search(r"عمري|مواليد|انولدت|ولدت|how old am i|born in", q):
            said = next((n for n in nums if 5 <= n <= 110), None)   # «عمري 21»: the age itself was given
            if not dates and not any(1900 < n <= today.year for n in nums) and said:
                return ToolResult(True, f"🎂 عمرك **{said} سنة**، يعني وُلدت حوالي سنة **{today.year - said}**" if ar else
                                  f"🎂 You are **{said}**, so you were born around **{today.year - said}**")
            born = dates[0] if dates else date(next(n for n in nums if 1900 < n <= today.year), 7, 1)
            years = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
            exact = bool(dates)
            return ToolResult(True, (f"🎂 العمر: **{years} سنة**" + ("" if exact else " (تقريباً، حسب سنة الميلاد)")) if ar else
                              f"🎂 Age: **{years}**" + ("" if exact else " (approx., from the birth year)"))
        if len(dates) >= 2:
            days = abs((dates[1] - dates[0]).days)
            return ToolResult(True, f"📅 بين التاريخين **{days} يوم** (≈ {days / 7:.1f} أسبوع)" if ar else
                              f"📅 **{days} days** between the dates (≈ {days / 7:.1f} weeks)")
        if dates:
            return ToolResult(True, f"📅 {question.strip('؟? ')}: **{_fmt(dates[0], ar)}**")
        if re.search(r"بعد|from now|later", q) and nums:
            target = today + timedelta(days=nums[0])
            return ToolResult(True, f"📅 بعد {nums[0]} يوم يكون التاريخ: **{_fmt(target, ar)}**" if ar else
                              f"📅 {nums[0]} days from now: **{_fmt(target, ar)}**")
    except (httpx.HTTPError, KeyError, ValueError, StopIteration) as exc:
        return ToolResult(False, f"ما قدرت أحسب التاريخ: {exc}" if ar else f"Couldn't work out the date: {exc}")
    return ToolResult(False, "حدّد التاريخ أو المناسبة، مثلاً: كم باقي على رمضان؟" if ar else "Name a date or event, e.g. days until Ramadan")
