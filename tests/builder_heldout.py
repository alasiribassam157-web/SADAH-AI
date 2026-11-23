"""Held-out requests (v30), written after v29 was promoted and aimed at what a real user would type but my sets never did: a request with no kind word at all, a name that is a common noun, a typo in «باسم», two kinds in one request, a very long request, and a plain refusal. NOT MEASURED YET: measure once, record the number here, promote into tests/builder_cases_k.py (or a new
part), write v31.
Earlier sets (all promoted after measuring): v1 15/20, v2 16/20, v3 14/16, v4 10/10, v5 19/20, v6 13/14, v7 16/17, v8 13/16, v9 8/15,
v10 9/14, v11 10/15, v12 10/13, v13 11/13, v14 12/13, v15 13/14, v16 10/11, v17 5/11, v18 9/12, v19 20/30 (from web research on what people
ask for), v20 15/15, v21 12/14, v22 12/14, v23 25/30 (from research on how people write Arabic online), v24 10/12, v25 7/10, v26 10/10,
v27 10/10, v28 9/10, v29 10/10; phrasing mine.
Never tune the rules on a case here without first moving it into SUITE and writing a fresh held-out set."""
from tests.builder_requests import case

HELDOUT = [
    case("landing", "ابغى شي لمطعم باسم المذاق الاصيل", name="المذاق الاصيل"),
    case("blog", "ابي مدونة باسم ورق", name="ورق"),
    case("landing", "موقع لمحل ورد باصم زهور", name="زهور"),
    case("shop", "ابي متجر باسم حياة فيه فيتامين 50 وزيت 35 وعسل 80", name="حياة", items_n=3),
    case("webapp", "ابغى تطبيق عداد باسم خطوات", name="خطوات", app="counter"),
    case("game", "لعبة ذاكرة باسم الحيوانات", name="الحيوانات", game="memory"),
    case("dashboard", "داشبورد باسم النمو فيه 2024 100 و2025 160", name="النمو", data_labels=["2024", "2025"]),
    case("event", "حفلة عيد ميلاد باسم يوسف الساعة 4 عصرا في البيت", name="يوسف", time="4 عصرا"),
    case("landing", "السلام عليكم ورحمة الله ابي موقع لمكتب هندسي باسم اتقان وخدماتنا تصميم واشراف وتنفيذ ولونه ازرق ودوامنا من 8 صباحا الى 5 مساء وجوالي 0501234567", name="اتقان"),
    case("refuse", "ابغى لعبة فيها دفع بالعملات"),
]
