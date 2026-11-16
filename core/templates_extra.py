"""SADAH v4 additions to the router data: prayer times, translation, sports, and more dialects.

Merged into templates_router.TEMPLATES / SLOTS at import time.
"""

SLOTS = {
    "word": ["cat", "water", "coffee", "book", "friend", "falcon", "computer", "good morning", "thank you",
             "قطة", "ماء", "قهوة", "كتاب", "صديق", "صقر", "حاسوب", "صباح الخير", "شكرا", "مدرسة", "سيارة"],
    "team": ["Real Madrid", "Barcelona", "Manchester City", "Liverpool", "Al Hilal", "Al Nassr",
             "ريال مدريد", "برشلونة", "الهلال", "النصر", "الاتحاد", "الأهلي", "مانشستر سيتي", "ليفربول"],
    "player": ["Cristiano Ronaldo", "Lionel Messi", "Mohamed Salah", "Kylian Mbappe", "Karim Benzema",
               "كريستيانو رونالدو", "ليونيل ميسي", "محمد صلاح", "كيليان مبابي", "كريم بنزيما", "سالم الدوسري"],
}

TEMPLATES = {
    "prayer": [
        "مواقيت الصلاة في {city}", "متى اذان المغرب في {city}", "وقت صلاة الفجر في {city}", "متى صلاة الظهر",
        "مواقيت الصلاة اليوم", "كم باقي على الاذان", "متى العشاء في {city}", "اوقات الصلاة {city}",
        "متى يأذن العصر", "prayer times in {city}", "when is maghrib in {city}", "fajr time in {city}",
        "what time is isha", "prayer times today", "شو مواعيد الصلاة في {city}", "مواعيد الصلاة في {city} ايه",
    ],
    "translate": [
        "ترجم {word}", "ترجم {word} للانجليزي", "ترجم {word} للعربي", "وش معنى {word} بالعربي",
        "وش معنى {word} بالانجليزي", "كيف اقول {word} بالانجليزي", "{word} بالانجليزي", "{word} بالعربي",
        "translate {word}", "translate {word} to arabic", "translate {word} to english", "how do you say {word} in arabic",
        "what is {word} in arabic", "what does {word} mean in english", "شو يعني {word} بالانجليزي",
        "يعني ايه {word} بالعربي", "ايش معنى كلمة {word}",
    ],
    "web": [
        "من مدرب {team}", "ملعب {team}", "في اي دوري يلعب {team}", "متى تأسس نادي {team}", "من مؤسس {team}",
        "في اي نادي يلعب {player}", "وش مركز {player}", "متى ولد {player}", "اخبرني عن {player}",
        "who is the coach of {team}", "stadium of {team}", "what league is {team} in", "which team does {player} play for",
        "what position does {player} play", "who is {player}",
        # Levantine & Egyptian question styles
        "شو هو {topic}", "شو هي {topic}", "شو يعني {topic}", "مين هو {topic}", "قديش عدد سكان {topic}",
        "وين بيقع {topic}", "ايه هو {topic}", "ايه هي {topic}", "مين اخترع {topic}", "فين يقع {topic}",
        "امتى اتأسست {topic}", "كام عدد سكان {topic}", "عايز اعرف عن {topic}", "بدي اعرف عن {topic}",
    ],
    "chat": ["مرحبتين", "كيفك شو الاخبار", "ازيك", "عامل ايه", "يسلمو", "تسلم", "متشكر", "اهلين", "صباحو", "تمام الحمد لله"],
    "python": ["قديش {n} ضرب {n}", "كام {n} زائد {n}", "احسبلي {n} ضرب {n}", "عايز احسب {n} قسمة {n}"],
    "weather": ["كيف الطقس بـ {city}", "شو الطقس في {city}", "الجو عامل ايه في {city}", "الدنيا حر في {city}؟"],
    "currency": ["قديش سعر ال{cur}", "الـ{cur} بكام", "بكام {n} {cur}", "سعر ال{cur} النهارده"],
    "datetime": ["قديش الساعة", "الساعة كام", "النهارده كام", "شو التاريخ اليوم"],
    "code": ["بدي كود {task} ب{lang}", "عايز كود {task} في {lang}", "ازاي {task} في {lang}", "كيف بعمل {task} ب{lang}"],
}
