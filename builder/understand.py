"""Arabic request -> Spec by rules. Asks one short question when something essential is missing,
and says plainly when a request is outside what the builder can make (it never invents).
Matching ignores hamza/alef variants (أ إ آ ا) and ى/ي, because people type them interchangeably."""
import re
from dataclasses import dataclass

from builder import content, facts
from builder.products import products
from builder.norm import n as _n
from builder.spec import COLORS, DEFAULT_ACCENT, Spec

SUPPORTED = ("المتاح حاليًا: موقع تعريفي، لوحة بيانات، متجر عرض، ملف أعمال، مدونة، دعوة فعالية، "
             "وتطبيق ويب صغير (قائمة مهام أو نموذج تسجيل).")
OUT_OF_SCOPE = ("اندرويد", "ايفون", "دفع", "قاعدة بيانات", "تسجيل دخول", "حجز", "سيرفر", "ذكاء",
                "دردشة", "محادثة", "شات", "اموال", "تحويل", "ارسال",
                # features that need a server or live data: said plainly, never silently dropped
                "سلة مشتريات", "سلة التسوق", "بث مباشر", "اشعارات", "تعليقات", "كوبونات", "مزاد",
                "مدفوع", "اشتراك شهري", "كاشير", "نقاط البيع", "تنبيهات", "ترجمة تلقائية", "ترجمة فورية", "مزامنة", "حساب", "حسابات", "عضوية", "تتبع", "توصيل للطلبات", "توصيل الطلبات", "استقبال الطلبات", "تقييمات", "مراجعات", "نشرة بريدية", "خريطة", "خرائط", "نظام نقاط", "بحث متقدم")
SECTION_WORDS = {"about": ("من نحن", "عن الشركة", "نبذة"), "services": ("خدمات", "خدماتنا"),
                 "gallery": ("معرض صور", "صور", "ألبوم"), "pricing": ("أسعار", "باقات", "تسعير"),
                 "testimonials": ("آراء", "تقييمات", "شهادات"), "contact": ("اتصال", "تواصل", "واتساب")}
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩٫", "0123456789.")


_MARKERS = {_n(w) for w in ("باسم", "اسمه", "اسمها", "اسم", "واسمه", "واسمها")}
_STOP = {_n(w) for w in (
    "وفيه", "وفيها", "فيه", "فيها", "ويكون", "ولونه", "لونه", "باللون", "وأبغى", "وابغى", "ابغى", "أبغى", "وأبي", "وابي",
    "ويحتوي", "يحتوي", "ولون", "لون", "مع", "على", "و", "وبيانات", "بيانات", "ولونها", "لونها", "لبيع", "للبيع", "يبيع",
    "ببيع", "وبيع")}
_EDGE = "«»\"“”،,.؟!:؛"
_SECTION_SKIP = {_n(w) for ws in SECTION_WORDS.values() for w in ws} | {_n("واتساب")}
_PERIOD = "(?:ال[أا]سبوع|الشهر|اليوم|الربع|السنة|[أا]سبوع|شهر|يوم|ربع|سنة)"
_PAIR = re.compile(rf"((?:{_PERIOD}\s+)?[ء-ي]+)\s*[:=]?\s*(\d+(?:\.\d+)?)")
_PAGE_WORDS = {"portfolio": ("ملف شخصي", "ملف أعمال", "معرض أعمال", "بورتفوليو", "portfolio", "أعمالي"),
               "blog": ("مدونة", "مدونتي", "مقالاتي", "مقالات"),
               "event": ("دعوة", "فعالية", "حفل", "مؤتمر", "مناسبة", "ملتقى", "زفاف", "ندوة", "محاضرة")}
# whole words only (with the usual one-letter prefixes and ال): "دفع" must not match "دفعة" (a graduating class)
_OUT = [(w, re.compile(rf"(?<![ء-ي])(?:[وفبك]?(?:ال)?|[وف]?لل|[وف]?ل){re.escape(_n(w))}(?![ء-ي])")) for w in OUT_OF_SCOPE]
# a date, time or place after the name ends it («زفاف سلمى يوم الخميس», «اسمها الرؤية في الرياض»; so a name
# with «في» in the middle is cut there, a known limit); kept apart from _STOP because weekdays are also dashboard labels
_WHEN = {_n(w) for w in ("يوم", "بتاريخ", "الساعة", "في", "نقدم", "نوفر", "خدماتنا", "مهاراتي", "نبيع", "منتجاتنا", "جوالي", "جوال",
                                          "رقم", "رقمي", "واتساب", "ايميل", "ايميلنا", "ايميلي", "بريدنا", "نعمل", "دوامنا", "دوام", "السبت", "الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة")}
_PERIOD_WORD = re.compile(_PERIOD)
_ABBR = re.compile(r"[ء-ي]{1,2}\.")
_YEAR = re.compile(r"(?:19|20)\d\d")
_MOBILE = re.compile(r"تطبيق(?:ات)?\s+(?:ل)?(?:ال)?جوال")


@dataclass
class Understood:
    spec: Spec | None
    question: str = ""
    unsupported: str = ""


def _has(text: str, words) -> bool:
    return any(_n(w) in text for w in words)


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
                if any(c.isdigit() for c in bare):
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


def _pairs(text: str) -> list[tuple[str, float]]:
    out = []
    for label, num in _PAIR.findall(text):
        label = label[1:] if label.startswith("و") and len(label) > 3 else label
        if _n(label) not in _MARKERS and _n(label) not in _STOP:
            out.append((label, float(num)))
    return out


def _kind(norm: str) -> str:
    if _has(norm, ("لوحة", "داشبورد", "dashboard")):
        return "dashboard"
    if _has(norm, ("متجر إلكتروني", "متجر الكتروني")) or (_has(norm, ("متجر",)) and "موقع" not in norm):
        return "shop"
    if "موقع" not in norm and _has(norm, ("تطبيق", "نموذج تسجيل", "نموذج اشتراك", "قائمة مهام")):
        return "webapp"
    for kind, words in _PAGE_WORDS.items():   # «ملف أعمال لمصورة … تصوير منتجات» is a portfolio, not a shop
        if _has(norm, words):
            return kind
    return "shop" if _has(norm, ("منتجات", "منتجاتي")) else "landing"


def _app(norm: str) -> str:
    if _has(norm, ("مهام", "مهمة", "قائمة")):
        return "tasks"
    return "register" if _has(norm, ("تسجيل", "نموذج", "اشتراك")) else ""


def understand(request: str) -> Understood:
    text = " ".join(request.translate(_DIGITS).split())
    norm = _n(text).lower()
    got = facts.extract(text, _SECTION_SKIP)   # phone / e-mail / hours leave the text, so they are never names or numbers
    name = _name(got.text)
    # a name after «باسم» is a label, not a feature request («ندوة الذكاء»); only an explicit marker earns this
    # (two words at most: «حوالات يرسل اموال» is a name that swallowed a feature request)
    asked = norm.replace(_n(name), " ", 1) if name and len(name.split()) <= 2 else norm
    hit = next((w for w, rx in _OUT if rx.search(asked)), "") or ("جوال" if _MOBILE.search(asked) else "")
    if hit:
        return Understood(None, unsupported=f"طلب «{hit}» غير مدعوم بعد. {SUPPORTED}")
    kind = _kind(norm)
    label, _, _ = content.for_business(text)
    spec = Spec(kind=kind, business=label if kind == "landing" else "", name=name,
                facts=got.facts, services=got.services)
    spec.accent = next((hex_ for ar, hex_ in COLORS.items() if _n(ar) in norm), DEFAULT_ACCENT)
    if kind == "landing":
        found = {s for s, ws in SECTION_WORDS.items() if _has(norm, ws)}
        spec.sections = [s for s in ("about", "services", "gallery", "pricing", "testimonials", "contact")
                         if s in {"about", "services", "contact"} | found]
    elif kind == "webapp":
        spec.app = _app(norm)
        if not spec.app:
            return Understood(None, unsupported=f"هذا النوع من التطبيقات غير مدعوم بعد. {SUPPORTED}")
    elif kind == "shop":
        spec.sections = ["contact"]
        spec.items = [(n, f"{int(v) if v.is_integer() else v} ريال") for n, v in products(got.text)] or [(x, "") for x in got.services]
    elif kind == "dashboard":
        pairs = _pairs(got.text)
        spec.data = pairs if len(pairs) >= 2 else []
    return Understood(spec, question="" if spec.name else "ما اسم المشروع؟")
