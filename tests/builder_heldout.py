"""Held-out requests (v18), written after v17 was promoted and before looking at how the rules treat them: apps and games
described in everyday Gulf wording, requests that mix a new app or game with an old feature, and near-misses that must stay
what they were. NOT MEASURED YET: measure once, record the number here, promote into tests/builder_cases_e.py, write v19.
Earlier sets (all promoted after measuring): v1 15/20, v2 16/20, v3 14/16, v4 10/10, v5 19/20, v6 13/14, v7 16/17,
v8 13/16, v9 8/15, v10 9/14, v11 10/15, v12 10/13, v13 11/13, v14 12/13, v15 13/14, v16 10/11, v17 5/11.
Never tune the rules on a case here without first moving it into SUITE and writing a fresh held-out set."""
from tests.builder_requests import case

HELDOUT = [
    case("webapp", "ابغى شي اعد فيه كم مرة قلت سبحان الله باسم عدّني", name="عدّني", app="counter"),
    case("webapp", "تطبيق يذكرني كم وقت بقي للاختبار باسم العد التنازلي", name="العد التنازلي", app="timer"),
    case("webapp", "ابي تطبيق اسجل فيه كم صرفت على القهوة باسم قهوتي ولونه ذهبي", name="قهوتي", app="expenses", accent="#a16207"),
    case("webapp", "تطبيق عادات للرياضة والقراءة باسم نمط", name="نمط", app="habits"),
    case("webapp", "ابغى تطبيق ملاحظات بسيط باسم مسودة", name="مسودة", app="notes"),
    case("game", "ابي لعبة اسئلة جغرافيا باسم عواصم", name="عواصم", game="quiz", topic="geography"),
    case("game", "لعبة اسئلة علمية باسم مختبر ولونها ازرق", name="مختبر", game="quiz", topic="science", accent="#1d4ed8"),
    case("game", "ابغى لعبة 2048 ولونها بنفسجي", game="g2048", accent="#6d28d9"),
    case("game", "لعبة التقاط الاشياء الساقطة باسم سلتي", name="سلتي", game="catch"),
    case("landing", "موقع لمدرسة حساب ذهني باسم عقول", name="عقول"),
    case("shop", "متجر باسم حاسبات وفيه حاسبة علمية 80 وحاسبة جيب 25", name="حاسبات", items_n=2),
    case("refuse", "لعبة اسئلة تسجل اسمي وتحفظ نتيجتي في حسابي"),
]
