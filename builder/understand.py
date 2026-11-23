"""Arabic request -> Spec by rules. Asks one short question when something essential is missing,
and says plainly when a request is outside what the builder can make (it never invents).
Matching ignores hamza/alef variants (أ إ آ ا) and ى/ي, because people type them interchangeably."""
import re
from dataclasses import dataclass

from builder import aliases, appword, content, facts, gameword, quizbank, themeword
from builder.products import products
from builder.naming import _name, _pairs, strip_name
from builder.norm import n as _n
from builder.spec import COLORS, DEFAULT_ACCENT, Spec

SUPPORTED = ("المتاح حاليًا: موقع تعريفي، لوحة بيانات، متجر عرض، ملف أعمال، مدونة، دعوة فعالية، "
             "وتطبيقات ويب صغيرة (قائمة مهام، حاسبة، عدّاد، مؤقت، مصروفات، ملاحظات، محوّل وحدات، عادات، نموذج تسجيل)، "
             "وألعاب (ذاكرة، تخمين رقم، إكس أو، أسئلة، ثعبان، 2048، التقاط، تحدي حساب).")
OUT_OF_SCOPE = ("اندرويد", "ايفون", "دفع", "قاعدة بيانات", "تسجيل دخول", "حجز", "سيرفر", "ذكاء",
                "دردشة", "محادثة", "شات", "اموال", "تحويل", "ارسال",
                # features that need a server or live data: said plainly, never silently dropped
                "سلة مشتريات", "سلة التسوق", "نظام تذاكر", "بنكي", "اونلاين", "اون لاين", "متصدرين", "ثلاثية الابعاد", "بث مباشر", "اشعارات", "تعليقات", "كوبونات", "مزاد",
                "العملات", "عملات", "سعر الصرف", "اسعار الصرف", "الاسهم", "البورصة", "كريبتو", "لعبة كلمات", "كلمات متقاطعة", "باتل رويال", "بوبجي", "فورتنايت", "فري فاير", "مدفوع", "اشتراك شهري", "كاشير", "نقاط البيع", "تنبيهات", "ترجمة تلقائية", "ترجمة فورية", "مزامنة", "حساب", "حسابات", "عضوية", "تتبع", "توصيل للطلبات", "توصيل الطلبات", "استقبال الطلبات", "تقييمات", "مراجعات", "نشرة بريدية", "خريطة", "خرائط", "نظام نقاط", "بحث متقدم")
SECTION_WORDS = {"about": ("من نحن", "عن الشركة", "نبذة"), "services": ("خدمات", "خدماتنا"),
                 "gallery": ("معرض صور", "صور", "ألبوم"), "pricing": ("أسعار", "باقات", "تسعير"),
                 "testimonials": ("آراء", "تقييمات", "شهادات"), "contact": ("اتصال", "تواصل", "واتساب")}
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩٫", "0123456789.")


_SECTION_SKIP = {_n(w) for ws in SECTION_WORDS.values() for w in ws} | {_n("واتساب")}
_PAGE_WORDS = {"portfolio": ("سيرة ذاتية", "ملف شخصي", "ملف أعمال", "معرض أعمال", "بورتفوليو", "portfolio", "أعمالي"),
               "blog": ("مدونة", "مدونتي", "مقالاتي", "مقالات"),
               "event": ("دعوة", "فعالية", "حفل", "مؤتمر", "مناسبة", "ملتقى", "زفاف", "ندوة", "محاضرة")}
# whole words only (with the usual one-letter prefixes and ال): "دفع" must not match "دفعة" (a graduating class)
_OUT = [(w, re.compile(rf"(?<![ء-ي])(?:[وفبك]?(?:ال)?|[وف]?لل|[وف]?ل){re.escape(_n(w))}(?:ي|نا|ك)?(?![ء-ي])")) for w in OUT_OF_SCOPE]   # «حسابي», «حجزك» (not ه: ة is normalised to ه, «دفعة» is not «دفع»)
_MOBILE = re.compile(r"تطبيق(?:ات)?\s+(?:ل)?(?:ال)?جوال")


@dataclass
class Understood:
    spec: Spec | None
    question: str = ""
    unsupported: str = ""


def _has(text: str, words) -> bool:
    return any(_n(w) in text for w in words)


def _kind(norm: str) -> str:
    if _has(norm, ("لوحة", "داشبورد", "dashboard")):
        return "dashboard"
    if _has(norm, ("متجر إلكتروني", "متجر الكتروني")) or (_has(norm, ("متجر",)) and "موقع" not in norm):
        return "shop"
    if _has(norm, ("صفحة هبوط", "لاندنج", "landing")):   # «صفحة هبوط لتطبيق توصيل» is a page about an app, not an app
        return "landing"
    if "موقع" not in norm and (re.search(r"تطبيق(?!ات)", norm) or _has(norm, ("نموذج تسجيل", "نموذج اشتراك", "قائمة مهام"))):   # «لمطور تطبيقات» is not an app
        return "webapp"
    for kind, words in _PAGE_WORDS.items():   # «ملف أعمال لمصورة … تصوير منتجات» is a portfolio, not a shop
        if _has(norm, words):
            return kind
    if "موقع" not in norm and appword.detect(norm):   # «ابغى حاسبة»: an app named without the word «تطبيق»
        return "webapp"
    return "shop" if _has(norm, ("منتجات", "منتجاتي")) else "landing"


def _app(norm: str) -> str:
    if _has(norm, ("مهام", "مهمة", "قائمة")):
        return "tasks"
    return "register" if _has(norm, ("تسجيل", "نموذج", "اشتراك")) else ""


def _game(norm: str, name: str, got, accent: str) -> Understood:
    """A game: which one is the only essential question; the title defaults to the game's own name."""
    game = gameword.detect(norm)
    if not game:
        return Understood(None, question="أي لعبة تبي؟ ذاكرة، تخمين رقم، إكس أو، أسئلة، ثعبان، 2048، التقاط، أو تحدي حساب.")
    topic = gameword.topic(norm) if game == "quiz" else "general"
    title = f"مسابقة {quizbank.TOPICS[topic][0]}" if topic != "general" else gameword.TITLES[game]
    return Understood(Spec(kind="game", game=game, topic=topic, name=name or title, accent=accent, facts=got.facts))



def understand(request: str) -> Understood:
    text = aliases.clean(" ".join(request.translate(_DIGITS).split()))
    norm = aliases.read(_n(text).lower())
    got = facts.extract(text, _SECTION_SKIP)   # phone / e-mail / hours leave the text, so they are never names or numbers
    name = _name(got.text)
    # a name after «باسم» is a label, not a feature request («ندوة الذكاء»); only an explicit marker earns this
    # (two words at most: «حوالات يرسل اموال» is a name that swallowed a feature request)
    asked = norm.replace(_n(name), " ", 1) if name and len(name.split()) <= 2 else norm
    asked = asked.replace(_n("تحويل الوحدات"), " ").replace(_n("تحويل وحدات"), " ")   # unit conversion is an app, money transfer is not
    asked = re.sub(rf"{_n('حساب')}\s+(?:سريع|ذهني)", " ", asked)   # a quick-maths game is not «حساب» (an account)
    asked = re.sub(rf"{_n('تتبع')}\s+(?:ال)?(?:مصروف|مصاريف|عاد|ميزاني)", " ", asked)   # tracking expenses or habits is an app, not order tracking
    asked = re.sub(rf"(?:{_n('ايفون')}|{_n('اندرويد')})\s+\d+", " ", asked)   # «ايفون 3500» is a product in a shop, not an iPhone app
    if not gameword.wants_game(asked):
        asked = re.sub(rf"{_n('اونلاين')}|{_n('اون لاين')}", " ", asked)   # «متجر اونلاين» is a normal site; online play is a game feature
    hit = next((w for w, rx in _OUT if rx.search(asked)), "") or ("جوال" if _MOBILE.search(asked) else "")
    if hit:
        return Understood(None, unsupported=f"طلب «{hit}» غير مدعوم بعد. {SUPPORTED}")
    accent = next((hex_ for ar, hex_ in COLORS.items() if _n(ar) in norm), DEFAULT_ACCENT)
    bare = strip_name(norm, name)   # the project name is a label, not a request
    theme, colour = themeword.detect(bare), any(_n(ar) in norm for ar in COLORS)
    if gameword.wants_game(bare):
        made = _game(bare, name, got, accent)
        if made.spec:
            made.spec = themeword.with_theme(made.spec, theme, colour)
            made.spec.art = themeword.art_flag(bare) is not False
        return made
    kind = _kind(norm)
    label, _, _ = content.for_business(text)
    spec = Spec(kind=kind, business=label if kind == "landing" else "", name=name,
                facts=got.facts, services=got.services)
    spec.accent = accent
    if kind == "landing":
        found = {s for s, ws in SECTION_WORDS.items() if _has(norm, ws)}
        spec.sections = [s for s in ("about", "services", "gallery", "pricing", "testimonials", "contact")
                         if s in {"about", "services", "contact"} | found]
    elif kind == "webapp":
        spec.app = "tasks" if _has(norm, ("مهام", "مهمة")) else appword.detect(norm) or _app(norm)
        if not spec.app and not name and len(norm.split()) <= 3:
            return Understood(None, question=appword.ASK)
        if not spec.app:
            return Understood(None, unsupported=f"هذا النوع من التطبيقات غير مدعوم بعد. {SUPPORTED}")
    elif kind == "shop":
        spec.sections = ["contact"]
        spec.items = [(n, f"{int(v) if v.is_integer() else v} ريال") for n, v in products(got.text)] or [(x, "") for x in got.services]
    elif kind == "dashboard":
        pairs = _pairs(got.text)
        spec.data = pairs if len(pairs) >= 2 else []
    spec = themeword.with_theme(spec, theme, colour)
    spec.art = themeword.art_flag(bare) is not False
    return Understood(spec, question="" if spec.name else "ما اسم المشروع؟")
