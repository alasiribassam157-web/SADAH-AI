"""Held-out requests (v4) for the builder: natural phrasing, written before seeing how the rules behave.
The rules in builder/understand.py are tuned on tests/builder_requests.py only. First measurements before tuning:
  v1 15/20, v2 16/20, v3 14/16 (all then moved into SUITE). Known limit: a request for a feature the builder
  does not have is refused only when the feature word is in OUT_OF_SCOPE; otherwise the feature is silently dropped.
Never tune the rules on a case here without first moving it into SUITE and writing a fresh held-out set."""
from tests.builder_requests import case

HELDOUT = [
    case("landing", "ابغى موقع لمكتب محاسبة باسم الميزان وفيه خدمات", name="الميزان", sections=["services"]),
    case("landing", "موقع لحضانة اطفال اسمها براعم ولونه برتقالي", name="براعم", accent="#c2410c"),
    case("landing", "ابغى موقع باسم عبدالله وفيه نبذة", name="عبدالله", sections=["about"]),
    case("dashboard", "لوحة بيانات باسم الطلبات فيها اليوم 40 امس 35", name="الطلبات", data_labels=["اليوم", "امس"]),
    case("shop", "متجر باسم لمسة وفيه كعك 12 وبسكويت 8", name="لمسة", items_n=2),
    case("webapp", "تطبيق قائمة مهام باسم واجبات", name="واجبات", app="tasks"),
    case("webapp", "ابغى تطبيق نموذج اشتراك باسم مجلتي", name="مجلتي", app="register"),
    case("ask", "ابغى لوحة"),
    case("refuse", "ابغى موقع باسم دورات وفيه محادثة مع المدرب"),
    case("refuse", "ابغى موقع فيه ارسال اموال"),
]
