"""Held-out requests (v17), written BEFORE the new apps (calculator, counter, timer, expenses, notes, converter, habits),
the quiz topics and the new games (2048, catch, math) exist: so these measure the new features honestly. NOT MEASURED YET:
build the features, measure once, record the number here, promote into tests/builder_cases_e.py, then write v18.
Earlier sets (all promoted after measuring): v1 15/20, v2 16/20, v3 14/16, v4 10/10, v5 19/20, v6 13/14, v7 16/17,
v8 13/16, v9 8/15, v10 9/14, v11 10/15, v12 10/13, v13 11/13, v14 12/13, v15 13/14, v16 10/11.
Never tune the rules on a case here without first moving it into SUITE and writing a fresh held-out set."""
from tests.builder_requests import case

HELDOUT = [
    case("webapp", "ابغى حاسبة باسم حسابي", name="حسابي", app="calculator"),
    case("webapp", "تطبيق عداد للتسبيح باسم سبحتي", name="سبحتي", app="counter"),
    case("webapp", "ابي مؤقت للمذاكرة باسم ركز", name="ركز", app="timer"),
    case("webapp", "تطبيق لتتبع مصروفاتي باسم ميزانيتي", name="ميزانيتي", app="expenses"),
    case("webapp", "تطبيق ملاحظات باسم دفتري ولونه اخضر", name="دفتري", app="notes", accent="#15803d"),
    case("webapp", "ابغى تطبيق يحول بين الكيلو والرطل باسم محول", name="محول", app="converter"),
    case("webapp", "تطبيق عادات يومية باسم التزام", name="التزام", app="habits"),
    case("game", "لعبة اسئلة عن الفضاء باسم رواد", name="رواد", game="quiz", topic="space"),
    case("game", "ابغى لعبة 2048 باسم الارقام", name="الارقام", game="g2048"),
    case("game", "لعبة التقاط النجوم باسم نجمة", name="نجمة", game="catch"),
    case("game", "ابي تحدي حساب سريع باسم ذكي", name="ذكي", game="math"),
    case("refuse", "تطبيق مصروفات يربط حسابي البنكي"),
    case("ask", "ابغى تطبيق"),
]
