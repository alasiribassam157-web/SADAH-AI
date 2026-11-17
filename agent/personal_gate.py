"""Personal gate: «من أنا؟» / «وش اسمي» / «من أنتِ» are conversation, never a Wikipedia search.

`is_personal()` is the iron rule used by the critic (these questions never become web / kb / synthesis);
`answer()` is the reply, written from the visitor's own session memory (name, city, job, likes).
"""
import re

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


def is_personal(message: str) -> bool:
    return bool(_AR.search(message) or _EN.search(message))


def about_sadah(message: str) -> bool:
    return bool(_YOU.search(message))


def answer(st: dict, message: str, ar: bool) -> str | None:
    """The reply for a personal question from this visitor's memory, or None when it is not one."""
    if not is_personal(message) or about_sadah(message):
        return None
    name, city, job, likes = st["name"], st["city"], st["job"], "، ".join(st["likes"])
    where = re.search(r"وين|أين|اين|مدينتي|بلدي|where", message, re.I)
    if not name and not city and not job and not likes:
        st["awaiting"] = True   # the next short message is the name
        return ("أنت صديقي 🤍 لكنك لم تخبرني باسمك بعد، ما هو اسمك لأحفظه في ذاكرتي؟" if ar else
                "You're my friend 🤍 but you haven't told me your name yet. What's your name so I can remember it?")
    if where and city:
        return f"أنت من {city} 🏙" if ar else f"You're from {city} 🏙"
    parts = [(f"اسمك {name}" if ar else f"your name is {name}") if name else "",
             (f"من {city}" if ar else f"from {city}") if city else "",
             (f"تشتغل {job}" if ar else f"you work as {job}") if job else "",
             (f"تحب {likes}" if ar else f"you like {likes}") if likes else ""]
    known = "، ".join(p for p in parts if p) if ar else ", ".join(p for p in parts if p)
    return (f"أنت صديقي 🤍 وأعرف عنك: {known}." if ar else f"You're my friend 🤍 and I know: {known}.")
