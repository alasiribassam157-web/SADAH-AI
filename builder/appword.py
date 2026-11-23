"""The small apps the builder can make and the Arabic words that name each one."""
import re

from builder.norm import n

TITLES = {"tasks": "قائمة مهام", "register": "نموذج تسجيل", "calculator": "حاسبة", "counter": "عداد", "timer": "مؤقت",
          "expenses": "مصروفات", "notes": "ملاحظات", "converter": "محوّل وحدات", "habits": "عادات"}
WORDS = {"expenses": ("مصروفات", "مصاريف", "مصروف", "ميزانية", "مصروفاتي", "صرفت", "أصرف"),
         "calculator": ("حاسبة", "آلة حاسبة", "calculator", "احسب", "أحسب"),
         "counter": ("عداد", "عدّاد", "تسبيح", "سبحة", "تسبيحة", "اسبح", "أسبح", "أسبّح"),
         "timer": ("مؤقت", "مؤقّت", "بومودورو", "تايمر", "عد تنازلي"),
         "notes": ("ملاحظات", "ملاحظة", "مذكرات", "اكتب", "أكتب", "أفكاري", "افكاري", "خواطر", "يوميات"),
         "converter": ("محول", "محوّل", "يحول", "احول", "أحول", "تحويل الوحدات", "تحويل وحدات", "الوحدات"), "habits": ("عادات", "عادة", "عاداتي")}
ASK = "أي تطبيق تبي؟ قائمة مهام، حاسبة، عدّاد، مؤقت، مصروفات، ملاحظات، محوّل وحدات، عادات، أو نموذج تسجيل."
_RX = {a: re.compile(r"(?<![ء-ي])[وفبل]?(?:ال)?(?:" + "|".join(re.escape(n(w)) for w in ws) + r")(?![ء-ي])") for a, ws in WORDS.items()}


def detect(norm: str) -> str:
    """The app named in a request (normalised text), or '' when none of the new apps is named."""
    return next((a for a, rx in _RX.items() if rx.search(norm)), "")
