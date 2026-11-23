"""What the assistant says: Arabic replies for the chat, built from the project's spec. No model: every sentence here is written by hand and
chosen by what the person said, so the same conversation always gets the same answer (and can be tested)."""
from builder import themes
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


def built(spec: Spec, new: bool, seed: str, note: str = "") -> str:
    ask = "تبي أعدّل شي؟ مثلًا: " + "، ".join(f"«{s}»" for s in missing(spec)[:3]) + "."
    if new:
        return f"{pick(['تمام، سويته لك!', 'أبشر، جاهز.', 'خلصت، شوف المعاينة.'], seed)} فهمت إنك تبي {summary(spec)} {ask}"
    return f"تم. {note} صار المشروع الحين: {summary(spec)} {ask}"


def ask_name(spec_kind_hint: str, seed: str) -> str:
    return pick(["حلو! وش اسم المشروع؟", "تمام، بس قل لي وش الاسم اللي تبيه له؟", "فهمت الفكرة. وش تحب نسميه؟"], seed)
