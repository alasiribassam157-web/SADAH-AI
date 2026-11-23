"""The games the builder can make: Arabic words that name each one, default titles, and switching a built game by an edit."""
import re
from dataclasses import replace

from builder.norm import n
from builder.spec import Spec

TITLES = {"memory": "لعبة الذاكرة", "guess": "خمّن الرقم", "xo": "إكس أو", "quiz": "مسابقة المعلومات", "snake": "لعبة الثعبان"}
WORDS = {"memory": ("ذاكرة", "بطاقات", "تطابق", "أزواج", "شبيه"), "guess": ("خمن", "تخمين", "خمّن", "رقم"),
         "xo": ("إكس أو", "اكس او", "xo", "x o", "أو إكس"), "quiz": ("أسئلة", "اسئلة", "سؤال", "مسابقة", "كويز", "اختبار", "معلومات"),
         "snake": ("ثعبان", "سنيك", "snake", "حية")}
_GAME = tuple(n(w) for w in ("لعبة", "ألعاب", "العاب", "game", "العب", "نلعب"))
# a site ABOUT games (a toy shop, a company) is not a game: these words mean a site, shop or page is wanted
_SITE = tuple(n(w) for w in ("موقع", "متجر", "محل", "شركة", "مكتب", "معرض", "ملف", "مدونة", "دعوة", "لوحة", "نادي", "مركز"))
_RX = {g: re.compile(r"(?<![ء-ي])(?:[وفبل]?(?:ال)?)(?:" + "|".join(re.escape(n(w)) for w in ws) + r")(?![ء-ي])") for g, ws in WORDS.items()}


def wants_game(norm: str) -> bool:
    """A request for a game itself: «لعبة …» without a word that makes it a site about games."""
    return any(re.search(rf"(?<![ء-ي])[وفبل]?(?:ال)?{w}(?![ء-ي])", norm) for w in _GAME) and not any(w in norm for w in _SITE)


def detect(norm: str) -> str:
    """The game named in a request (normalised text), or '' when none is named."""
    return next((g for g, rx in _RX.items() if rx.search(norm)), "")


def switch(spec: Spec, nt: str) -> tuple[Spec, list[str]]:
    """«غيّر اللعبة إلى ثعبان»: another game, and the default title follows when the old one was the default."""
    if spec.kind != "game" or not re.search(r"(?<![ء-ي])(?:غير|بدل|حول|خلي)", nt) or not (g := detect(nt)) or g == spec.game:
        return spec, []
    name = TITLES[g] if spec.name == TITLES.get(spec.game) else spec.name
    return replace(spec, game=g, name=name), [f"صارت اللعبة «{TITLES[g]}»"]
