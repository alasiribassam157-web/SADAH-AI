"""SADAH v5 benchmark additions: symbolic math, date reasoning, comparisons, compound questions (26)."""

CASES_V5 = [
    # --- symbolic math (12)
    ("حل المعادلة 2x+5=17", "python", "x = 6"), ("solve x^2 - 5x + 6 = 0", "python", "x = 3"),
    ("حل 3س - 7 = 2س + 4", "python", "x = 11"), ("حل x+y=10, x-y=2", "python", "y = 4"),
    ("مشتقة x^3 + 2x", "python", "3·x^2 + 2"), ("derivative of sin(x)*x", "python", "cos"),
    ("تكامل x^2 من 0 الى 3", "python", "9"), ("integrate 2x", "python", "x^2"),
    ("حلل x^2-9", "python", "(x - 3)·(x + 3)"), ("القاسم المشترك الأكبر لـ 48 و 180", "python", "12"),
    ("حلل 360 الى عوامله الأولية", "python", "2^3 × 3^2 × 5"), ("حول 255 الى ثنائي", "python", "11111111"),
    # --- date reasoning (6)
    ("كم باقي على رمضان", "datetime", "يوم"), ("how many days until eid al-adha", "datetime", "days"),
    ("كم عمري لو انولدت 12-05-1998", "datetime", "سنة"), ("كم يوم بين 2026-01-01 و 2026-03-15", "datetime", "73"),
    ("كم باقي على اليوم الوطني", "datetime", "سبتمبر"), ("اي يوم يوافق 1 يناير 2027", "datetime", "الجمعة"),
    # --- comparisons (5)
    ("قارن بين سكان مصر والسعودية", "web", "مصر"), ("ايهما اكبر مساحة السعودية ام الجزائر", "web", "الجزائر"),
    ("compare the population of Japan and Germany", "web", "Japan"),
    ("which is taller Burj Khalifa or Eiffel Tower", "web", "Burj Khalifa"),
    ("أيهما أطول جبل إيفرست ام جبل كليمنجارو", "web", "8,849"),
    # --- compound questions (3)
    ("ما هي عاصمة اليابان وكم عدد سكانها", "web", "نسمة"), ("who is Elon Musk and when was he born", "web", "1971"),
    ("ما هي عاصمة فرنسا وما هي عملتها", "web", "يورو"),
]
