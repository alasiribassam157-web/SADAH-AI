"""Held-out edit instructions (E4), written BEFORE it was ever run against builder/edit.py. The rules are tuned on
tests/builder_edit_suite.py only; this set is measured once, then promoted there and replaced by a fresh one.
Each case: (project request, instruction, expectations). `changed` says whether the project must change."""

SALON = "موقع لصالون حلاقة باسم الاناقة ولونه اخضر"
STORE = "متجر باسم بيت القهوة وفيه بن 60 وهيل 45"
CHART = "لوحة بيانات باسم الزيارات يناير 40 فبراير 55 مارس 61"

HELDOUT_EDITS = [
    (SALON, "حوله للون الاحمر", {"changed": True, "accent": "#b91c1c"}),
    (SALON, "تكفى اللون الاسود", {"changed": True, "accent": "#111827"}),
    (SALON, "عايز قسم الاسعار", {"changed": True, "sections_has": ["pricing"]}),
    (SALON, "لا اريد قسم من نحن", {"changed": True, "sections_not": ["about"]}),
    (SALON, "ضيف لي خدمة حلاقة اطفال", {"changed": True, "services_has": ["حلاقة اطفال"]}),
    (SALON, "عدل الاسم الى صالون الفخامة", {"changed": True, "name": "صالون الفخامة"}),
    (SALON, "واتساب 0501112233", {"changed": True, "phone": "0501112233"}),
    (SALON, "دوامنا من 10 صباحا الى 12 مساء", {"changed": True, "hours": "من 10 صباحا الى 12 مساء"}),
    (STORE, "اضف منتج قرفة 25", {"changed": True, "items_has": [("قرفة", "25 ريال")]}),
    (STORE, "احذف منتج بن", {"changed": True, "items_not": ["بن"]}),
    (CHART, "احذف فبراير", {"changed": True}),
    (SALON, "اضف كوبونات خصم", {"changed": False, "note_has": "غير مدعوم"}),
    (SALON, "؟؟؟", {"changed": False, "note_has": "ما فهمت"}),
    ("ملف شخصي باسم عمر", "غير الاسم الى عمر الحربي", {"changed": True, "name": "عمر الحربي"}),
    ("دعوة لحفل تخرج باسم دفعة 2026", "يوم الجمعة في قاعة النخيل", {"changed": True, "date": "الجمعة", "place": "قاعة النخيل"}),
    (SALON, "اضف قسم الصور وغير اللون الى الذهبي", {"changed": True, "sections_has": ["gallery"], "accent": "#a16207"}),
]
