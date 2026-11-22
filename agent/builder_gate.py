"""Chat -> builder. A message that asks SADAH to make a website or small app is recognised by rule, understood
by the builder's own rules, and answered here instead of by the 12-intent router (which saw «اصنع لي موقع»
as weather at 32%). No model: a creation verb plus a thing the builder can make, minus «where is…» phrasings.
The reply never contains generated files; it states what was understood and links /builder to preview and download."""
import re
import urllib.parse

from builder.understand import _n, understand

_MARKS = re.compile("[ً-ْـ]")
_STRONG = {_n(w) for w in ("اصنع", "اصنعي", "سو", "سوي", "صمم", "اعمل", "انشئ", "ابني", "بناء")}   # «make me …»
_WEAK = {_n(w) for w in ("ابغى", "ابي", "ابى", "ودي", "اريد", "اطلب")}            # «I want …»: needs a clearer thing
_THINGS = tuple(_n(t) for t in ("موقع", "مدونة", "متجر", "لوحة بيانات", "داشبورد", "تطبيق", "نموذج تسجيل", "دعوة",
                               "ملف شخصي", "بورتفوليو", "معرض أعمال", "صفحة"))
_CLEAR = tuple(_n(t) for t in ("مدونة", "متجر", "لوحة بيانات", "داشبورد", "تطبيق مهام", "نموذج تسجيل", "بورتفوليو",
                              "معرض أعمال", "موقع ل", "موقع باسم", "موقع تعريفي", "دعوة ل", "ملف شخصي ل"))
# whole words only: «كم» must not match inside «تحكم»
_WHERE = re.compile("(?<![ء-ي])(?:" + "|".join(_n(w) for w in (
    "وين", "اين", "أين", "أقرب", "قريب", "قرب", "عنوان", "رابط", "سعر", "كم", "ساعات", "مين", "من هو", "ما هو")) + ")(?![ء-ي])")
KIND = {"landing": "موقع تعريفي", "dashboard": "لوحة بيانات", "shop": "متجر عرض", "webapp": "تطبيق ويب",
        "portfolio": "ملف أعمال", "blog": "مدونة", "event": "دعوة فعالية"}
EXAMPLE = "ابغى موقع لمطعم باسم بيت الشواء ولونه أحمر"


def _norm(text: str) -> str:
    return _n(_MARKS.sub("", text)).lower()


def is_build_request(text: str) -> bool:
    norm = _norm(text)
    words = set(norm.split())
    if not re.search("[ء-ي]", norm) or _WHERE.search(norm):
        return False
    if words & _STRONG:
        return any(t in norm for t in _THINGS)
    return bool(words & _WEAK) and any(t in norm for t in _CLEAR)


def reply(text: str) -> str:
    """The chat answer for a build request, or "" when the message is something else."""
    if not is_build_request(text):
        return ""
    u = understand(text)
    if u.unsupported:
        return u.unsupported
    if u.question:
        return f"تمام، أقدر أبنيه لك. {u.question}\nاكتب الطلب كاملًا، مثل: «{EXAMPLE}»."
    link = "/builder?request=" + urllib.parse.quote(text.strip()[:1000], safe="")
    return (f"فهمت طلبك: **{KIND[u.spec.kind]}** باسم **{u.spec.name}**.\n"
            f"المعاينة والتنزيل (ملفات جاهزة بـ zip): [افتح المنشئ]({link})\n"
            "النصوص اللي ما ذكرتها تظهر بعلامة «(عدّل هذا النص)» لتعبّيها أنت.")
