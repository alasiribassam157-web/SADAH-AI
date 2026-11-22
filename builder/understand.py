"""Arabic request -> Spec by rules. Asks one short question when something essential is missing,
and says plainly when a request is outside what the builder can make (it never invents).
Matching ignores hamza/alef variants (أ إ آ ا) and ى/ي, because people type them interchangeably."""
import re
from dataclasses import dataclass

from builder import content
from builder.spec import COLORS, DEFAULT_ACCENT, Spec

SUPPORTED = "المتاح حاليًا: موقع تعريفي، لوحة بيانات، متجر عرض، وتطبيق ويب صغير (قائمة مهام أو نموذج تسجيل)."
OUT_OF_SCOPE = ("اندرويد", "ايفون", "دفع", "قاعدة بيانات", "تسجيل دخول", "حجز", "سيرفر", "ذكاء",
                "دردشة", "محادثة", "شات", "اموال", "تحويل", "ارسال")
SECTION_WORDS = {"about": ("من نحن", "عن الشركة", "نبذة"), "services": ("خدمات", "خدماتنا"),
                 "gallery": ("معرض صور", "صور", "ألبوم"), "pricing": ("أسعار", "باقات", "تسعير"),
                 "testimonials": ("آراء", "تقييمات", "شهادات"), "contact": ("اتصال", "تواصل", "واتساب")}
_ALEF = str.maketrans("أإآىة", "اااYه".replace("Y","ي"))
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩٫", "0123456789.")


def _n(s: str) -> str:
    return s.translate(_ALEF)


_MARKERS = {_n(w) for w in ("باسم", "اسمه", "اسمها", "اسم", "واسمه", "واسمها")}
_STOP = {_n(w) for w in (
    "وفيه", "وفيها", "فيه", "فيها", "ويكون", "ولونه", "لونه", "باللون", "وأبغى", "وابغى", "ابغى", "أبغى", "وأبي", "وابي",
    "ويحتوي", "يحتوي", "ولون", "لون", "مع", "على", "و", "وبيانات", "بيانات", "ولونها", "لونها", "لبيع", "للبيع", "يبيع",
    "ببيع", "وبيع")}
_EDGE = "«»\"“”،,.؟!:؛"
_PERIOD = "(?:ال[أا]سبوع|الشهر|اليوم|الربع|السنة|[أا]سبوع|شهر|يوم|ربع|سنة)"
_PAIR = re.compile(rf"((?:{_PERIOD}\s+)?[ء-ي]+)\s*[:=]?\s*(\d+(?:\.\d+)?)")
_MOBILE = re.compile(r"تطبيق(?:ات)?\s+(?:ل)?(?:ال)?جوال")


@dataclass
class Understood:
    spec: Spec | None
    question: str = ""
    unsupported: str = ""


def _has(text: str, words) -> bool:
    return any(_n(w) in text for w in words)


def _name(text: str) -> str:
    words = text.split()
    for i, w in enumerate(words):
        if _n(w.strip(_EDGE)) in _MARKERS:
            out = []
            for nxt in words[i + 1:i + 5]:
                bare = nxt.strip(_EDGE)
                if any(c.isdigit() for c in bare):
                    if out:
                        out.pop()  # the word before a number is a data label, not part of the name
                    break
                if not bare or _n(bare) in _STOP:
                    break
                out.append(bare)
                if nxt[-1] in _EDGE:
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
    if _has(norm, ("متجر إلكتروني", "متجر الكتروني")) or _has(norm, ("منتجات", "منتجاتي")) or (_has(norm, ("متجر",)) and "موقع" not in norm):
        return "shop"
    if "موقع" not in norm and _has(norm, ("تطبيق", "نموذج تسجيل", "قائمة مهام")):
        return "webapp"
    return "landing"


def _app(norm: str) -> str:
    if _has(norm, ("مهام", "مهمة", "قائمة")):
        return "tasks"
    return "register" if _has(norm, ("تسجيل", "نموذج", "اشتراك")) else ""


def understand(request: str) -> Understood:
    text = " ".join(request.translate(_DIGITS).split())
    norm = _n(text).lower()
    hit = next((w for w in OUT_OF_SCOPE if _n(w) in norm), "") or ("جوال" if _MOBILE.search(norm) else "")
    if hit:
        return Understood(None, unsupported=f"طلب «{hit}» غير مدعوم بعد. {SUPPORTED}")
    kind = _kind(norm)
    label, _, _ = content.for_business(text)
    spec = Spec(kind=kind, business=label if kind == "landing" else "", name=_name(text))
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
        spec.items = [(n, f"{int(v) if v.is_integer() else v} ريال") for n, v in _pairs(text)]
    else:
        pairs = _pairs(text)
        spec.data = pairs if len(pairs) >= 2 else []
    return Understood(spec, question="" if spec.name else "ما اسم المشروع؟")
