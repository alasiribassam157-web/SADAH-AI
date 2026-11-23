"""The games the builder can make: Arabic words that name each one, default titles, and switching a built game by an edit."""
import re
from dataclasses import replace

from builder import quizbank
from builder.norm import n

_PFX = r"(?:[وف]?لل|[وفبل]?(?:ال)?)"   # a one-letter prefix, ال, or «لل» (للمصاريف = لـ + المصاريف)
from builder.spec import Spec

TITLES = {"memory": "لعبة الذاكرة", "guess": "خمّن الرقم", "xo": "إكس أو", "quiz": "مسابقة المعلومات", "snake": "لعبة الثعبان",
          "g2048": "2048", "catch": "التقط النجوم", "math": "تحدي الحساب"}
WORDS = {"g2048": ("2048",), "catch": ("التقاط", "التقط", "اصطياد", "اصطاد", "صيد النجوم"), "math": ("تحدي حساب", "حساب سريع", "حساب ذهني", "رياضيات", "عمليات حسابية"),
         "memory": ("ذاكرة", "بطاقات", "تطابق", "أزواج", "شبيه", "اطابق", "أطابق", "طابق", "مطابقة"), "guess": ("خمن", "تخمين", "خمّن", "رقم"),
         "xo": ("إكس أو", "اكس او", "xo", "x o", "أو إكس"), "quiz": ("أسئلة", "اسئلة", "سؤال", "مسابقة", "كويز", "اختبار", "معلومات"),
         "snake": ("ثعبان", "سنيك", "snake", "حية")}
_GAME = tuple(n(w) for w in ("لعبة", "ألعاب", "العاب", "game", "العب", "نلعب"))
# a site ABOUT games (a toy shop, a company) is not a game: these words mean a site, shop or page is wanted
_WEAK = tuple(n(w) for w in ("تحدي", "مسابقة", "كويز"))   # «تحدي حساب سريع»: a game only when a game is also named
_SITE = tuple(n(w) for w in ("موقع", "متجر", "محل", "شركة", "مكتب", "معرض", "ملف", "مدونة", "دعوة", "لوحة", "نادي", "مركز"))
_RX = {g: re.compile(r"(?<![ء-ي])" + _PFX + r"(?:" + "|".join(re.escape(n(w)) for w in ws) + r")(?![ء-ي])") for g, ws in WORDS.items()}


_TOPIC = {t: re.compile(r"(?<![ء-ي])" + _PFX + r"(?:" + "|".join(re.escape(n(w)) for w in ws) + r")(?![ء-ي])") for t, ws in quizbank.WORDS.items()}


def topic(norm: str) -> str:
    """The quiz topic named in a request (normalised text); «general» when none is named."""
    return next((t for t, rx in _TOPIC.items() if rx.search(norm)), "general")


def wants_game(norm: str) -> bool:
    """A request for a game itself: «لعبة …» without a word that makes it a site about games. `norm` has the project name cut out."""
    word = lambda ws: any(re.search(rf"(?<![ء-ي]){_PFX}{w}(?![ء-ي])", norm) for w in ws)  # noqa: E731
    return (word(_GAME) or (word(_WEAK) and bool(detect(norm)))) and not any(w in norm for w in _SITE)


def detect(norm: str) -> str:
    """The game named in a request (normalised text), or '' when none is named."""
    return next((g for g, rx in _RX.items() if rx.search(norm)), "")


def switch(spec: Spec, nt: str) -> tuple[Spec, list[str]]:
    """«غيّر اللعبة إلى ثعبان»: another game, and the default title follows when the old one was the default."""
    if spec.kind != "game" or not re.search(r"(?<![ء-ي])(?:غير|بدل|حول|خلي)", nt):
        return spec, []
    if spec.game == "quiz" and (t := topic(nt)) != "general" and t != spec.topic:
        return replace(spec, topic=t), [f"صار موضوع المسابقة «{quizbank.TOPICS[t][0]}»"]
    if not (g := detect(nt)) or g == spec.game:
        return spec, []
    name = TITLES[g] if spec.name == TITLES.get(spec.game) else spec.name
    return replace(spec, game=g, name=name), [f"صارت اللعبة «{TITLES[g]}»"]
