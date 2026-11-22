"""Held-out requests (v9) for the builder, written before looking at how the rules treat them.
The rules in builder/understand.py are tuned on tests/builder_requests.py only. Measure once, then record the
number and promote these cases into SUITE. Earlier sets (all promoted after measuring):
  v1 15/20, v2 16/20, v3 14/16, v4 10/10, v5 19/20, v6 13/14, v7 16/17, v8 13/16.
Never tune the rules on a case here without first moving it into SUITE and writing a fresh held-out set."""
from tests.builder_requests import case

HELDOUT = [
    case("landing", "ابغى موقع لمركز رياضي باسم لياقة ولونه احمر وفيه اسعار", name="لياقة", accent="#b91c1c", sections=["pricing"]),
    case("landing", "ابغى موقع لصيدلية باسم الشفاء وفيه ساعات العمل", name="الشفاء"),
    case("landing", "موقع لمكتب سفريات اسمه آفاق ولونه ازرق", name="آفاق", accent="#1d4ed8"),
    case("dashboard", "لوحة بيانات باسم الاستخدام فيها واي فاي 20 كهرباء 55 ماء 30", name="الاستخدام", data_labels=["واي فاي", "كهرباء", "ماء"]),
    case("shop", "متجر باسم زهرة وفيه باقة ورد 80 وبوكيه 120", name="زهرة", items_n=2),
    case("webapp", "ابغى نموذج اشتراك بالنشرة باسم اخبار", name="اخبار", app="register"),
    case("portfolio", "ابغى ملف اعمال لمهندس باسم م. سعد", name="م. سعد"),
    case("blog", "مدونة لنشر قصصي القصيرة باسم حكايا", name="حكايا"),
    case("event", "ابغى دعوة لحفل خطوبة باسم خطوبة ريم وسلطان", name="خطوبة ريم وسلطان"),
    case("ask", "ابغى متجر الكتروني"),
    case("ask", "ابغى تطبيق مهام"),
    case("refuse", "ابغى موقع فيه اشتراك شهري مدفوع"),
    case("refuse", "ابغى متجر فيه تقييمات ومراجعات من العملاء"),
    case("refuse", "ابغى مدونة مع نشرة بريدية ترسل تلقائي"),
    case("refuse", "ابغى موقع فيه خريطة تفاعلية"),
]
