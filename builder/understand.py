"""Arabic request -> Spec by rules (stage 1). Asks one short question when something essential is missing."""
import re
from dataclasses import dataclass

from builder import content
from builder.spec import COLORS, DEFAULT_ACCENT, Spec

UNSUPPORTED = {"لوحة": "لوحة بيانات", "متجر": "متجر", "تطبيق": "تطبيق"}  # planned, not built yet
SECTION_WORDS = {"about": ("من نحن", "عن الشركة", "نبذة"), "services": ("خدمات", "خدماتنا"),
                 "gallery": ("معرض صور", "صور", "ألبوم"), "pricing": ("أسعار", "باقات", "تسعير"),
                 "testimonials": ("آراء", "تقييمات", "شهادات"), "contact": ("اتصال", "تواصل", "واتساب")}
_MARKERS = ("باسم", "اسمه", "اسمها", "اسم")
_STOP = {"وفيه", "وفيها", "فيه", "فيها", "ويكون", "ولونه", "لونه", "باللون", "وأبغى", "وابغى", "ابغى", "أبغى",
         "وأبي", "وابي", "ويحتوي", "يحتوي", "ولون", "لون", "مع", "على", "و"}
_EDGE = "«»\"“”،,.؟!:؛"


@dataclass
class Understood:
    spec: Spec | None
    question: str = ""
    unsupported: str = ""


def _name(text: str) -> str:
    words = text.split()
    for i, w in enumerate(words):
        if w.strip(_EDGE) in _MARKERS:
            out = []
            for nxt in words[i + 1:i + 5]:
                bare = nxt.strip(_EDGE)
                if not bare or bare in _STOP:
                    break
                out.append(bare)
                if nxt[-1] in _EDGE:
                    break
            return " ".join(out)
    return ""


def understand(request: str) -> Understood:
    text = " ".join(request.split())
    for word, label in UNSUPPORTED.items():
        if word in text and "موقع" not in text:
            return Understood(None, unsupported=f"«{label}» غير مدعوم بعد؛ المتاح حاليًا موقع تعريفي.")
    label, _, _ = content.for_business(text)
    found = {s for s, ws in SECTION_WORDS.items() if any(w in text for w in ws)}
    sections = _order({"about", "services", "contact"} | found)  # these three are always present
    accent = next((hex_ for ar, hex_ in COLORS.items() if ar in text), DEFAULT_ACCENT)
    name = _name(text)
    if not name:
        return Understood(Spec(business=label, sections=sections, accent=accent), question="ما اسم المشروع؟")
    return Understood(Spec(name=name, business=label, sections=sections, accent=accent))


def _order(sections) -> list[str]:
    order = ["about", "services", "gallery", "pricing", "testimonials", "contact"]
    return [s for s in order if s in sections]
