"""Project specification: the structured form of an Arabic request, shared by every template."""
from dataclasses import dataclass, field

KINDS = ("landing",)
SECTIONS = ("about", "services", "gallery", "pricing", "testimonials", "contact")
COLORS = {"أزرق": "#1d4ed8", "أخضر": "#15803d", "أحمر": "#b91c1c", "أسود": "#111827",
          "ذهبي": "#a16207", "بنفسجي": "#6d28d9", "برتقالي": "#c2410c"}
DEFAULT_ACCENT = "#1d4ed8"


@dataclass
class Spec:
    kind: str = "landing"
    name: str = ""
    business: str = ""
    sections: list[str] = field(default_factory=lambda: ["about", "services", "contact"])
    accent: str = DEFAULT_ACCENT
    lang: str = "ar"


def problems(spec: Spec) -> list[str]:
    """Reasons a spec cannot be built (empty list = buildable)."""
    out = []
    if spec.kind not in KINDS:
        out.append(f"نوع المشروع غير مدعوم بعد: {spec.kind}")
    if not spec.name.strip():
        out.append("اسم المشروع مفقود")
    bad = [s for s in spec.sections if s not in SECTIONS]
    if bad:
        out.append(f"أقسام غير معروفة: {', '.join(bad)}")
    if "contact" not in spec.sections:
        out.append("قسم التواصل مطلوب")
    if not (spec.accent.startswith("#") and len(spec.accent) == 7):
        out.append("لون غير صالح")
    return out
