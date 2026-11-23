"""What the assistant says: Arabic replies for the chat, built from the project's spec. No model: every sentence here is written by hand and
chosen by what the person said, so the same conversation always gets the same answer (and can be tested)."""
from builder import themes
from builder.ml import design
from builder.spec import COLORS, Spec

KIND = {"landing": "موقع تعريفي", "dashboard": "لوحة بيانات", "shop": "متجر عرض", "webapp": "تطبيق ويب", "portfolio": "ملف أعمال",
        "blog": "مدونة", "event": "دعوة فعالية", "game": "لعبة"}
APP = {"tasks": "قائمة مهام", "register": "نموذج تسجيل", "calculator": "حاسبة", "counter": "عدّاد", "timer": "مؤقت", "expenses": "تتبع مصروفات",
       "notes": "ملاحظات", "converter": "محوّل وحدات", "habits": "عادات"}
GAME = {"memory": "ذاكرة", "guess": "تخمين رقم", "xo": "إكس أو", "quiz": "أسئلة", "snake": "ثعبان", "g2048": "2048", "catch": "التقاط", "math": "تحدي حساب"}
SECTION = {"about": "من نحن", "services": "الخدمات", "gallery": "المعرض", "pricing": "الأسعار", "testimonials": "الآراء", "contact": "التواصل"}
COLOUR = {hex_: ar for ar, hex_ in COLORS.items()}
HELLO = ["هلا والله! وش تبي نبني اليوم؟ موقع أو تطبيق أو لعبة، قل لي بكلامك.", "أهلًا فيك! احكي لي وش في بالك وأنا أرتبه لك: موقع، تطبيق صغير، أو لعبة.",
         "يا هلا! وش الفكرة اللي عندك؟ ابدأ بأي طريقة وأنا أسألك عن الباقي."]
THANKS = ["العفو، وأي تعديل تبيه أنا حاضر.", "حياك الله! لو تبي تغيّر شي بالمشروع قل لي.", "تسلم! إذا خطر لك تعديل أو مشروع ثاني أنا هنا."]
CAN = ("أبني لك من جملة عربية: مواقع تعريفية، متاجر عرض، لوحات بيانات، ملفات أعمال، مدونات، دعوات فعاليات، تطبيقات صغيرة "
       "(مهام، حاسبة، عدّاد، مؤقت، مصروفات، ملاحظات، محوّل وحدات، عادات، نموذج تسجيل) وألعاب (ذاكرة، تخمين رقم، إكس أو، أسئلة، ثعبان، 2048، التقاط، تحدي حساب). "
       "وأعدّل اللي بنيته: اللون، الاسم، الأقسام، المنتجات، الشكل (فخم، داكن، بسيط، زجاجي). ما أسوي: دفع إلكتروني أو حسابات مستخدمين أو تطبيقات جوال.")
START = ["موقع لمطعم باسم السفرة", "متجر باسم الورد وفيه ورد 20 وشموع 35", "لعبة ذاكرة باسم نجوم", "تطبيق مصروفات باسم جيبي"]


def pick(options: list[str], seed: str) -> str:
    return options[sum(map(ord, seed)) % len(options)]


def what(spec: Spec) -> str:
    if spec.kind == "webapp":
        return f"تطبيق {APP.get(spec.app, '')}"
    if spec.kind == "game":
        return f"لعبة {GAME.get(spec.game, '')}"
    return KIND.get(spec.kind, spec.kind)


def summary(spec: Spec) -> str:
    """The requirements as the builder understood them, in one paragraph."""
    parts = [f"{what(spec)} باسم «{spec.name}»"]
    if spec.business:
        parts.append("لل" + spec.business[2:] if spec.business.startswith("ال") else "ل" + spec.business)
    parts.append(f"باللون {COLOUR.get(spec.accent, 'المختار')}" if spec.accent in COLOUR else "بلون مخصص")
    if spec.theme != "default":
        parts.append(f"بشكل {themes.LABELS[spec.theme]}")
    if spec.kind == "shop" and spec.items:
        parts.append(f"فيه {len(spec.items)} منتجات")
    if spec.kind == "dashboard" and spec.data:
        parts.append(f"بـ{len(spec.data)} قيم")
    if spec.kind in ("landing", "portfolio", "blog", "shop"):
        parts.append("وأقسامه: " + "، ".join(SECTION[s] for s in spec.sections if s in SECTION))
    if not spec.art:
        parts.append("بدون زخارف")
    return " ".join(parts) + "."


def missing(spec: Spec) -> list[str]:
    """Things a person usually wants and the request did not say, as ready-to-send suggestions."""
    out = []
    if spec.kind in ("landing", "shop", "portfolio") and not spec.facts.get("phone"):
        out.append("اضف رقم جوالي 0501234567")
    if spec.kind in ("landing", "shop") and "pricing" not in spec.sections and spec.kind == "landing":
        out.append("اضف قسم الاسعار")
    if spec.theme == "default":
        out.append("خله فخم")
    if spec.accent == "#1d4ed8":
        out.append("غير اللون الى اخضر")
    return out[:4] or ["غير اللون الى بنفسجي", "خله زجاجي"]


FIELDS = ("design", "phone", "colour", "theme")
QUESTION = {"phone": "تبي أحط رقم جوال للتواصل؟ اكتبه هنا، أو قل «لا».",
            "colour": "وش اللون اللي يعجبك؟ أزرق، أخضر، أحمر، أسود، ذهبي، بنفسجي، برتقالي. أو قل «لا» وأخليه كذا.",
            "theme": "وش الشكل اللي تبيه؟ فخم، داكن، بسيط، زجاجي. أو قل «لا» وأخليه كذا."}
CHOICES = {"design": ["طبّقه", "لا"], "phone": ["لا"], "colour": ["أخضر", "أحمر", "بنفسجي", "لا"], "theme": ["فخم", "داكن", "زجاجي", "لا"]}
DONE = "هذا كل اللي أسألك عنه. جرّب المشروع، وقل لي لو تبي أي تعديل ثاني."


def question(field: str, spec: Spec, about: str = "") -> str:
    """The question for a field; the design one explains the model's reading of the project."""
    s = design.suggest(spec, about) if field == "design" else None
    if not s:
        return QUESTION.get(field, "")
    words = "، ".join(f"«{w}»" for w in s.because)
    return (f"من كلامك فهمت إن مشروعك من مجال «{s.label}» (من {words}). {s.why}. أقترح لك اللون {COLOUR.get(s.accent, 'الذهبي')} "
            f"{'بالشكل المعتاد' if s.theme == 'default' else 'وشكل ' + themes.LABELS[s.theme]}. أطبّقه؟")


def next_field(spec: Spec, skipped: tuple, about: str = "") -> str:
    """The next thing worth asking about: what the request left out and the person has not waved away."""
    for f in FIELDS:
        if f in skipped:
            continue
        if f == "design" and not design.decided(spec) and design.suggest(spec, about):
            return f
        if f == "phone" and spec.kind in ("landing", "shop", "portfolio") and not spec.facts.get("phone"):
            return f
        if f == "colour" and spec.accent == "#1d4ed8" and spec.kind != "game":
            return f
        if f == "theme" and spec.theme == "default":
            return f
    return ""


def built(spec: Spec, new: bool, seed: str, note: str = "", field: str = "", about: str = "") -> str:
    ask = question(field, spec, about) if field else DONE
    if new:
        return f"{pick(['تمام، سويته لك!', 'أبشر، جاهز.', 'خلصت، شوف المعاينة.'], seed)} فهمت إنك تبي {summary(spec)} {ask}"
    return f"تم. {note} صار المشروع الحين: {summary(spec)} {ask}"


def ask_name(spec_kind_hint: str, seed: str) -> str:
    return pick(["حلو! وش اسم المشروع؟", "تمام، بس قل لي وش الاسم اللي تبيه له؟", "فهمت الفكرة. وش تحب نسميه؟"], seed) + " وإذا ما عندك فكرة قل «اقترح لي»."


NO_DOMAIN = "ما قدرت أعرف مجال مشروعك من كلامي معك. قل لي وش نشاطك (مطعم، عيادة، مكتب…) وأقترح لك الأنسب."


def name_ideas(picks: list[str]) -> str:
    return "اقتراحاتي لك: " + "، ".join(f"«{x}»" for x in picks) + ". اختر واحد منها أو اكتب اسمك."
