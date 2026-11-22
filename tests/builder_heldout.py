"""Held-out requests (v8) for the builder, written before looking at how the rules treat them.
The rules in builder/understand.py are tuned on tests/builder_requests.py only. Measure once, then record the
number and promote these cases into SUITE. Earlier sets (all promoted after measuring):
  v1 15/20, v2 16/20, v3 14/16, v4 10/10, v5 19/20, v6 13/14, v7 16/17.
Never tune the rules on a case here without first moving it into SUITE and writing a fresh held-out set."""
from tests.builder_requests import case

HELDOUT = [
    case("landing", 'ابغى موقع لمقهى باسم "نجوم" وفيه الاسعار', name="نجوم", sections=["pricing"]),
    case("landing", "أبغى موقع لشركة باسم Alpha Tech", name="Alpha Tech"),
    case("landing", "ابغى موقع لمطعم باسم المذاق وفية تواصل", name="المذاق"),
    case("landing", "موقع تعريفي لشركة اسمها الرؤية في الرياض", name="الرؤية"),
    case("dashboard", "ابغى داشبورد باسم الايرادات فيها الربع الاول 500 الربع الثاني 650", name="الايرادات", data_labels=["الربع الاول", "الربع الثاني"]),
    case("shop", "ابي متجر باسم مكتبتي وفيه كتاب ٢٠ ريال وقلم ٥ ريال", name="مكتبتي", items_n=2),
    case("webapp", "ابغى تطبيق قائمة مهام باسم اولوياتي ولونه اسود", name="اولوياتي", app="tasks", accent="#111827"),
    case("portfolio", "ابغى بورتفوليو لمصورة باسم لقطة ولونها اسود", name="لقطة", accent="#111827"),
    case("blog", "ابي مدونة اكتب فيها مقالات عن الصحة باسم عافية", name="عافية"),
    case("event", "دعوة لحفل استقبال مولود باسم مولودنا الجديد", name="مولودنا الجديد"),
    case("event", "موقع لفعالية رياضية باسم ماراثون الرياض الساعة 5", name="ماراثون الرياض"),
    case("ask", "ابغى مدونة عن السفر"),
    case("ask", "ابغى موقع لمطعم البيك"),
    case("refuse", "ابغى متجر فيه سلة مشتريات"),
    case("refuse", "ابغى تطبيق ايفون وموقع باسم رحلتي"),
    case("refuse", "ابغى مدونة فيها بث مباشر"),
]
