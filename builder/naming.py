"""Names and numbers in an Arabic request: where a project name starts and ends, and label/number pairs."""
import re

from builder.norm import n as _n

_MARKERS = {_n(w) for w in ("باسم", "اسمه", "اسمها", "اسم", "واسمه", "واسمها")}
_STOP = {_n(w) for w in (
    "وفيه", "وفيها", "فيه", "فيها", "ويكون", "ولونه", "لونه", "باللون", "وأبغى", "وابغى", "ابغى", "أبغى", "وأبي", "وابي",
    "ويحتوي", "يحتوي", "ولون", "لون", "مع", "على", "و", "وبيانات", "بيانات", "ولونها", "لونها", "لبيع", "للبيع", "يبيع",
    "ببيع", "وبيع", "بدون", "بلا", "شغلنا", "نصنع", "نسوي", "تخصصنا", "نشتغل", "متجر", "موقع", "تطبيق", "لعبة", "مدونة", "جزاك", "اتمنى", "ياليت", "يارب", "ان", "شكرا", "يعطيك", "تسلم", "بسرعة", "ممكن", "لو", "وبس", "ستايل", "بستايل", "طابع", "بطابع", "اجواء", "باجواء", "وضع", "بالوضع", "فخم", "فخمة", "فاخر", "فاخرة", "داكن", "داكنة", "دارك", "مينيمال", "ثيم", "بثيم", "تصميم", "بتصميم", "شكل", "بشكل", "نمط", "بنمط")}
_EDGE = "«»\"“”،,.؟!:؛"
_PERIOD = "(?:ال[أا]سبوع|الشهر|اليوم|الربع|السنة|[أا]سبوع|شهر|يوم|ربع|سنة)"
_PAIR = re.compile(rf"((?:{_PERIOD}\s+)?[ء-ي]+)\s*[:=]?\s*(\d+(?:\.\d+)?)")
# a date, time or place after the name ends it («زفاف سلمى يوم الخميس», «اسمها الرؤية في الرياض»; so a name
# with «في» in the middle is cut there, a known limit); kept apart from _STOP because weekdays are also dashboard labels
_WHEN = {_n(w) for w in ("يوم", "بتاريخ", "الساعة", "في", "نقدم", "نوفر", "خدماتنا", "مهاراتي", "نبيع", "منتجاتنا", "جوالي", "جوال",
                                          "رقم", "رقمي", "جوالنا", "رقمنا", "واتسابنا", "معرض", "معرضي", "اعمالي", "اعمالنا", "عن", "لدينا", "عندنا", "واتساب", "ايميل", "ايميلنا", "ايميلي", "بريدنا", "نعمل", "دوامنا", "دوام", "السبت", "الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة")}
_PERIOD_WORD = re.compile(_PERIOD)
_ABBR = re.compile(r"[ء-ي]{1,2}\.")
_YEAR = re.compile(r"(?:19|20)\d\d")
def _ends(w: str) -> bool:
    """A word that ends a name; also when a و is glued to it («وخدماتنا», «وواتساب»)."""
    return w in _STOP or w in _WHEN or (w.startswith("و") and (w[1:] in _STOP or w[1:] in _WHEN))


def _name(text: str) -> str:
    words = text.split()
    for i, w in enumerate(words):
        if _n(w.strip(_EDGE)) in _MARKERS:
            out = []
            for nxt in words[i + 1:i + 5]:
                bare = nxt.strip(_EDGE)
                if _YEAR.fullmatch(bare) and out:
                    out.append(bare)  # a year after a name word is part of the name (تخرج 2026), not data
                    break
                if out and _PERIOD_WORD.fullmatch(_n(bare)) and any(c.isdigit() for t in words[i + 2 + len(out):i + 4 + len(out)] for c in t):
                    break  # «المصروفات الاسبوع الاول 300»: the period word starts the first data label
                if re.fullmatch(r"\d+(?:\.\d+)?", bare):
                    if out:
                        out.pop()  # the word before a number is a data label, not part of the name
                    break
                if not bare or (out and _ends(_n(bare))):  # the first word is the name even if it is a stop word (لون)
                    break
                abbr = bool(_ABBR.fullmatch(nxt))  # a title such as «د.» keeps its dot and does not end the name
                out.append(nxt if abbr else bare)
                if nxt[-1] in _EDGE and not abbr:
                    break
            return " ".join(out)
    return ""


def strip_name(norm: str, name: str) -> str:
    """The normalised request without the project name: the name right after its marker, not an earlier look-alike
    («باسم الليل» must not cut the «الليل» out of «الليلي»)."""
    if not name:
        return norm
    marker = "|".join(sorted(_MARKERS, key=len, reverse=True))
    out, count = re.subn(rf"(?<![ء-ي])({marker})\s+{re.escape(_n(name))}", r"\1 ", norm, count=1)
    return out if count else norm.replace(_n(name), " ", 1)


def _pairs(text: str) -> list[tuple[str, float]]:
    out = []
    for label, num in _PAIR.findall(text):
        label = label[1:] if label.startswith("و") and len(label) > 3 else label
        if _n(label) not in _MARKERS and _n(label) not in _STOP:
            out.append((label, float(num)))
    return out
