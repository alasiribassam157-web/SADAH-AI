"""Held-out requests (v26), written after v25 was promoted: the «لل» prefix on other words, what the business does after the name, the kind word
right after the name, decoration switched off in the request, and fresh domains. NOT MEASURED YET: measure once, record the number here,
promote into tests/builder_cases_g.py (or a new part), write v27.
Earlier sets (all promoted after measuring): v1 15/20, v2 16/20, v3 14/16, v4 10/10, v5 19/20, v6 13/14, v7 16/17, v8 13/16, v9 8/15,
v10 9/14, v11 10/15, v12 10/13, v13 11/13, v14 12/13, v15 13/14, v16 10/11, v17 5/11, v18 9/12, v19 20/30 (from web research on what people
ask for), v20 15/15, v21 12/14, v22 12/14, v23 25/30 (from research on how people write Arabic online), v24 10/12, v25 7/10; phrasing mine.
Never tune the rules on a case here without first moving it into SUITE and writing a fresh held-out set."""
from tests.builder_requests import case

HELDOUT = [
    case("webapp", "ابغى تطبيق للملاحظات اليومية باسم خاطرة", name="خاطرة", app="notes"),
    case("game", "ابغى لعبة للذاكرة باسم تذكر", name="تذكر", game="memory"),
    case("landing", "ابي موقع لمكتب هندسي باسم اساس وتخصصنا تصميم وتنفيذ في الرياض", name="اساس", city="الرياض"),
    case("shop", "مكتبة صغيرة باسم حروف متجر وفيها رواية 40 وديوان 30", name="حروف", items_n=2),
    case("landing", "موقع لعيادة باسم نبض بدون زخارف", name="نبض"),
    case("blog", "مدونة للطبخ باسم نكهة", name="نكهة"),
    case("dashboard", "لوحة بيانات للمبيعات باسم تقدمنا فيها الاسبوع الاول 80 الاسبوع الثاني 95", name="تقدمنا", data_labels=["الاسبوع الاول", "الاسبوع الثاني"]),
    case("event", "دعوة لحفل زفاف باسم لمى وبدر الساعة 9 مساء في قاعة الورد", name="لمى وبدر", time="9 مساء"),
    case("webapp", "تطبيق للعادات اليومية باسم التزامي", name="التزامي", app="habits"),
    case("refuse", "ابغى متجر فيه كاشير ونقاط بيع"),
]
