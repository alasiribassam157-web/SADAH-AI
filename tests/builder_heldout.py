"""Held-out requests (v25), written after v24 was promoted: a look and a colour in dialect, English app names, a game with a topic written loosely,
a long story-style message, and telegraphic messages. NOT MEASURED YET: measure once, record the number here, promote into
tests/builder_cases_g.py (or a new part), write v26.
Earlier sets (all promoted after measuring): v1 15/20, v2 16/20, v3 14/16, v4 10/10, v5 19/20, v6 13/14, v7 16/17, v8 13/16, v9 8/15,
v10 9/14, v11 10/15, v12 10/13, v13 11/13, v14 12/13, v15 13/14, v16 10/11, v17 5/11, v18 9/12, v19 20/30 (from web research on what people
ask for), v20 15/15, v21 12/14, v22 12/14, v23 25/30 (from research on how people write Arabic online), v24 10/12; phrasing mine, not real users.
Never tune the rules on a case here without first moving it into SUITE and writing a fresh held-out set."""
from tests.builder_requests import case

HELDOUT = [
    case("landing", "ابي موقع فخفخينا لمحل مجوهرات باسم درة", name="درة"),
    case("shop", "متجر شنط باسم حقيبتي وفيه شنطة ظهر 150 وشنطة يد 220 ولونه بنفسجي", name="حقيبتي", items_n=2, accent="#6d28d9"),
    case("webapp", "ابغى app للمصاريف باسم Spend", name="Spend", app="expenses"),
    case("game", "لعبة كويز عن الحيوانات باسم غابة", name="غابة", game="quiz", topic="animals"),
    case("landing", "والله ابغى موقع لورشة نجارة عندي في جدة باسم خشب وشغلنا ابواب ومطابخ ورقمي 0561234567", name="خشب", city="جدة", phone="0561234567"),
    case("shop", "كوب 30 وصحن 20 باسم بيتي متجر", name="بيتي", items_n=2),
    case("event", "حفل تخرج باسم دفعة 2027 يوم الاربعاء الساعة 7 مساء", name="دفعة 2027", date="الاربعاء", time="7 مساء"),
    case("blog", "ابغى مدونة باسم يوميات طالب ثيم هادئ", name="يوميات طالب", theme="simple"),
    case("dashboard", "داشبورد باسم الايرادات يناير 100 فبراير 120", name="الايرادات", data_labels=["يناير", "فبراير"]),
    case("refuse", "ابغى لعبة اونلاين مع الاصدقاء باسم تحدي"),
]
