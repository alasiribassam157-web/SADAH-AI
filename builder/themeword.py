"""The look a request asks for («موقع فخم», «ثيم داكن», «تصميم بسيط»), and the edit that switches it."""
import re
from dataclasses import replace

from builder import themes
from builder.norm import n
from builder.spec import COLORS, DEFAULT_ACCENT, Spec

_B = r"(?<![ء-ي])(?:[وف]?لل|[وفب]?(?:ال)?)"
_E = r"(?![ء-ي])"
_CTX = "(?:تصميم|ثيم|شكل|وضع|ستايل|نمط|خلفيه|مظهر)"
# a word that is a look by itself, and a word that is one only after «تصميم / ثيم / شكل …» («تطبيق بسيط» is a small app, «ازرق داكن» is a colour)
_SOLO = {"dark": ("دارك", "dark", "ليلي", "مظلم", "داكن", "داكنة", "مظلمة", "ليلية"), "luxe": ("فخم", "فخمة", "فاخر", "فاخرة", "راقي", "راقية", "ملكي", "ملكية", "لاكشري", "luxury", "luxe"),
         "simple": ("مينيمال", "minimal", "نظيف", "نظيفة", "هادئ", "هادئة", "هادي"), "light": ()}
_NEEDS_CONTEXT = {"dark": ("اسود", "غامق"), "light": ("فاتح", "ابيض", "نهاري", "light"), "simple": ("بسيط", "بسيطه")}
_COLOUR_SHADE = re.compile(rf"(?:{'|'.join(n(c) for c in COLORS)})\s+(?:داكن|غامق|فاتح)")
_RX = {t: re.compile(rf"{_B}(?:{'|'.join(map(n, ws))}){_E}") for t, ws in _SOLO.items() if ws}
_CTX_RX = {t: re.compile(rf"{_CTX}\s+(?:ال)?(?:{'|'.join(map(n, ws))}){_E}") for t, ws in _NEEDS_CONTEXT.items()}
_DECOR = r"(?:ال)?(?:زخارف|زخرفه|زخرفات|رسومات|ديكور|تزيين)"
_OFF = re.compile(rf"(?<![ء-ي])(?:بدون|بلا|شيل|احذف|ازل|الغ|الغي|امسح)\s+{_DECOR}")
_ON = re.compile(rf"(?<![ء-ي])(?:اضف|زود|حط|ضيف|رجع|ارجع)\s+{_DECOR}")
_VERB = re.compile(r"(?<![ء-ي])(?:غير|بدل|خلي|خل|حول|اجعل|صير|ابغى|ابي|نبي)")


def detect(norm: str) -> str:
    """The theme named in a request (normalised text); «default» when none is named."""
    norm = _COLOUR_SHADE.sub(" ", norm)
    for t in themes.PALETTE:
        if t in _CTX_RX and _CTX_RX[t].search(norm) or t in _RX and _RX[t].search(norm):
            return t
    return "default"


def with_theme(spec: Spec, theme: str, explicit_colour: bool) -> Spec:
    """The spec in a theme; the luxe look takes gold unless the request names a colour."""
    new = replace(spec, theme=theme)
    return replace(new, accent=themes.LUXE_GOLD) if theme == "luxe" and not explicit_colour and spec.accent == DEFAULT_ACCENT else new


def switch(spec: Spec, nt: str) -> tuple[Spec, list[str]]:
    """«خله فخم», «غير الثيم الى داكن»: the instruction (normalised) changes the theme."""
    notes = []
    flag = art_flag(nt)
    if flag is not None and flag != spec.art:
        spec = replace(spec, art=flag)
        notes.append("أضفت الزخارف" if flag else "أزلت الزخارف")
    theme = detect(nt)
    if theme == "default" or theme == spec.theme or not _VERB.search(nt):
        return spec, notes
    return with_theme(spec, theme, False), notes + [f"صار الشكل «{themes.LABELS[theme]}»"]


def art_flag(nt: str) -> bool | None:
    """«بدون زخارف» -> False, «أضف زخارف» -> True, nothing said -> None (normalised text)."""
    return False if _OFF.search(nt) else True if _ON.search(nt) else None
