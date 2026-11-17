"""Personal gate: «من أنا؟» / «وش اسمي» / «من أنتِ» are conversation, never a Wikipedia search.

`is_personal()` is the iron rule used by the critic (these questions never become web / kb / synthesis);
`answer()` is the reply, written from the visitor's own session memory (name, city, job, likes).
"""
import re
from datetime import datetime

_AR = re.compile(
    r"(?<!\w)(?:من|مين|منو|منهو)\s+(?:أنا|انا)(?!\w)|(?<!\w)(?:من|مين)\s+(?:أنت|انت|أنتِ|انتي|أنتي)(?!\w)|"
    r"(?:وش|ايش|شو|ما|ماهو|ما هو)\s+(?:اسمي|إسمي)|(?<!\w)(?:اسمي|إسمي)\s+(?:ايش|وش|شو)|"
    r"(?:تتذكر(?:ين|ي)?|تعرف(?:ين|ي)?|تذكر(?:ين|ي)?)\s+(?:اسمي|إسمي|من انا|من أنا)|"
    r"(?:وين|أين|اين)\s+(?:أسكن|اسكن|ساكن|أعيش|اعيش)|(?<!\w)(?:مدينتي|بلدي|وظيفتي|شغلي)(?!\w)|"
    r"(?:كيف|شلون)\s+(?:حالي|أنا|انا)(?!\w)|(?:عرف(?:ي|ين)ني|عرفيني)\s+(?:ب)?نفسك|"
    r"(?:وش|ايش|شو)\s+(?:تعرف(?:ين|ي)?|تتذكر(?:ين|ي)?)\s+عني", re.I)
_EN = re.compile(r"\bwho am i\b|\bwhat(?:'s| is) my name\b|\bdo you (?:remember|know) (?:me|my name)\b|"
                 r"\bwhere do i live\b|\bwho are you\b|\bintroduce yourself\b|\btell me about yourself\b", re.I)
_YOU = re.compile(r"(?:من|مين)\s+(?:أنت|انت|أنتِ|انتي|أنتي)|عرف(?:ي|ين)ني\s+(?:ب)?نفسك|who are you|introduce yourself|"
                  r"tell me about yourself", re.I)


_AGE_ASK = re.compile(r"(?:كم|عرفت كم|تعرف كم|تعرفين كم)\s+(?:عمري|سني)|متى\s+(?:انولدت|ولدت)|how old am i|when was i born", re.I)
_YEAR = re.compile(r"(?<!\d)(?:19\d\d|20[0-2]\d)(?!\d)")   # a birth year the date skill can compute from
_AGE = re.compile(r"^(?:انا\s+|أنا\s+)?عمري\s+(\d{1,3})(?:\s*(?:سنه|سنة|عام|year|years))?$|^i(?:'m| am)\s+(\d{1,3})(?: years old)?$", re.I)
_BORN = re.compile(r"^(?:انا\s+|أنا\s+)?(?:مواليد|مولود|انولدت|ولدت|ولدت في|انولدت في)(?:\s+(?:سنة|سنه|عام))?\s+(19\d\d|20[0-2]\d)$|"
                   r"^i was born in\s+(19\d\d|20[0-2]\d)$", re.I)
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def asks_age(message: str) -> bool:
    """«كم عمري» with nothing to compute from — the visitor's own age, kept in their memory (a full date goes to date_math)."""
    return bool(_AGE_ASK.search(message)) and not _YEAR.search(message.translate(_DIGITS))


def is_personal(message: str) -> bool:
    return bool(_AR.search(message) or _EN.search(message) or asks_age(message))


def capture_age(st: dict, message: str, ar: bool) -> str | None:
    """«عمري 21 سنه» / «انا مواليد 2005» (or a bare number after we asked) are remembered, not computed."""
    text, year = re.sub(r"[.!؟?،,\s]+$", "", message.strip()).translate(_DIGITS), datetime.now().year
    who = f" يا {st['name']}" if st["name"] else ""
    if m := _BORN.match(text):
        born = int(next(g for g in m.groups() if g))
        age = year - born
        st.update(birth_year=str(born), age=str(age), awaiting_age=False)
        return f"مواليد {born}، يعني عمرك الآن حوالي **{age} سنة** 🎂 حفظتُ ذلك في ذاكرتي!"
    m = _AGE.match(text) or (re.fullmatch(r"(\d{1,3})", text) if st.get("awaiting_age") else None)
    if m and 5 <= (age := int(next(g for g in m.groups() if g))) <= 110:
        st.update(age=str(age), birth_year=str(year - age), awaiting_age=False)
        return f"العمر كله{who}! حفظتُ في ذاكرتي أن عمرك {age} سنة 🎂"
    if st.get("awaiting_age") and (m := re.fullmatch(r"(19\d\d|20[0-2]\d)", text)):
        return capture_age(st, f"مواليد {m.group(1)}", ar)
    return None


def about_sadah(message: str) -> bool:
    return bool(_YOU.search(message))


def answer(st: dict, message: str, ar: bool) -> str | None:
    """The reply for a personal question from this visitor's memory, or None when it is not one."""
    if not is_personal(message) or about_sadah(message):
        return None
    if asks_age(message):
        if st.get("age"):
            return f"عمرك **{st['age']} سنة** 🎂"
        st["awaiting_age"] = True
        return "لم تخبرني بعمرك أو سنة ميلادك بعد 😊 كم عمرك أو في أي سنة وُلدت لأحفظها في ذاكرتي؟"
    name, city, job, likes, age = st["name"], st["city"], st["job"], "، ".join(st["likes"]), st.get("age", "")
    where = re.search(r"وين|أين|اين|مدينتي|بلدي|where", message, re.I)
    if not (name or city or job or likes or age):
        st["awaiting"] = True   # the next short message is the name
        return ("أنت صديقي 🤍 لكنك لم تخبرني باسمك بعد، ما هو اسمك لأحفظه في ذاكرتي؟" if ar else
                "You're my friend 🤍 but you haven't told me your name yet. What's your name so I can remember it?")
    if where and city:
        return f"أنت من {city} 🏙" if ar else f"You're from {city} 🏙"
    parts = [(f"اسمك {name}" if ar else f"your name is {name}") if name else "",
             (f"من {city}" if ar else f"from {city}") if city else "",
             (f"تشتغل {job}" if ar else f"you work as {job}") if job else "",
             (f"تحب {likes}" if ar else f"you like {likes}") if likes else "",
             (f"عمرك {age} سنة" if ar else f"you are {age}") if age else ""]
    known = "، ".join(p for p in parts if p) if ar else ", ".join(p for p in parts if p)
    return (f"أنت صديقي 🤍 وأعرف عنك: {known}." if ar else f"You're my friend 🤍 and I know: {known}.")
