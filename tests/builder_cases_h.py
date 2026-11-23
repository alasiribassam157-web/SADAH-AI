"""Builder requests, part H: held-out v26 (10/10 measured once before any tuning; a clean run on a set aimed at the previous failures,
so it says little about unseen phrasing)."""
from tests.builder_case import case

CASES = [
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
