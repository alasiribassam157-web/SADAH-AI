"""Held-out requests (v7) for the builder, written before looking at how the rules treat them.
The rules in builder/understand.py are tuned on tests/builder_requests.py only. Measure once, then record the
number and promote these cases into SUITE. Earlier sets (all promoted after measuring):
  v1 15/20, v2 16/20, v3 14/16, v4 10/10, v5 19/20, v6 13/14.
Never tune the rules on a case here without first moving it into SUITE and writing a fresh held-out set."""
from tests.builder_requests import case

HELDOUT = [
    case("landing", "عاوز صفحة لمحل ورد اسمه روز", name="روز"),
    case("landing", "ابغى موقع لحلويات باسم السكر وفيه من نحن واتصال", name="السكر", sections=["about", "contact"]),
    case("landing", "ابغى موقع لورشة سيارات باسم الميكانيكي وفيه تواصل", name="الميكانيكي"),
    case("dashboard", "لوحة بيانات باسم المتوسط فيها يناير 10.5 فبراير 20.25", name="المتوسط", data_labels=["يناير", "فبراير"]),
    case("shop", "متجر باسم الخير وفيه تمر 30 ريال وقهوة 45 ريال", name="الخير", items_n=2),
    case("shop", "ابغى متجر باسم ركن الهدايا ولونه ذهبي", name="ركن الهدايا", accent="#a16207"),
    case("webapp", "ابغى تطبيق ويب لادارة المهام باسم مرتب", name="مرتب", app="tasks"),
    case("portfolio", "ابغى portfolio باسم نور", name="نور"),
    case("portfolio", "ابغى موقع لعرض اعمالي كمبرمج باسم كود", name="كود"),
    case("blog", "مدونة شخصية باسم خواطر", name="خواطر"),
    case("event", "دعوة لعقد قران باسم ليلة العمر", name="ليلة العمر"),
    case("event", "موقع لحفلة عيد ميلاد باسم عيد ريم ولونه بنفسجي", name="عيد ريم", accent="#6d28d9"),
    case("event", "دعوة لحفل زفاف باسم زفاف سلمى يوم الخميس", name="زفاف سلمى"),
    case("ask", "ابغى موقع لمعرض اعمال"),
    case("ask", "ابغى موقع لدفعة الثانوية"),
    case("refuse", "ابغى مدونة مع قاعدة بيانات للقراء"),
    case("refuse", "ابغى مدونة وتطبيق اندرويد"),
]
