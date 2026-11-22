"""Held-out requests (v10) for the builder, written BEFORE the facts pillar existed: facts stated inside the request
(services, phone, e-mail, city, hours, an event's date / time / place) must reach the site instead of placeholders.
The rules are tuned on tests/builder_requests.py only. Measure once, then record the number and promote.
Earlier sets (all promoted after measuring): v1 15/20, v2 16/20, v3 14/16, v4 10/10, v5 19/20, v6 13/14,
v7 16/17, v8 13/16, v9 8/15 (unsupported features without a refusal word; a two-word dashboard label stays a known limit).
Never tune the rules on a case here without first moving it into SUITE and writing a fresh held-out set."""
from tests.builder_requests import case

HELDOUT = [
    case("landing", "ابغى موقع لمغسلة سيارات باسم لمعان وخدماتنا غسيل داخلي وتلميع وتنظيف محرك وجوالي 0501234567",
         name="لمعان", services=["غسيل داخلي", "تلميع", "تنظيف محرك"], phone="0501234567"),
    case("landing", "موقع لعيادة اسنان باسم الابتسامة في جدة ورقم الهاتف 0555123456", name="الابتسامة", city="جدة", phone="0555123456"),
    case("landing", "موقع لمطعم باسم المذاق ايميلنا info@mathaq.com ونعمل من 9 صباحا الى 11 مساء",
         name="المذاق", email="info@mathaq.com", hours="من 9 صباحا الى 11 مساء"),
    case("landing", "ابغى موقع لمكتب محاماة باسم الحق نقدم استشارات وصياغة عقود وقضايا تجارية",
         name="الحق", services=["استشارات", "صياغة عقود", "قضايا تجارية"]),
    case("landing", "موقع لصالون باسم فخامة وواتساب +966501234567 في الرياض", name="فخامة", phone="+966501234567", city="الرياض"),
    case("landing", "موقع لمقهى باسم ركن القهوة", name="ركن القهوة", services=[]),
    case("shop", "متجر باسم عبق وفيه بخور 50 ودهن عود 200 وجوالي 0501112222", name="عبق", items_n=2, phone="0501112222"),
    case("event", "دعوة لحفل زفاف باسم زفاف نورة وفهد يوم الخميس الساعة 8 مساء في قاعة الماسة",
         name="زفاف نورة وفهد", date="الخميس", time="8 مساء", place="قاعة الماسة"),
    case("event", "موقع لملتقى باسم ملتقى الاعمال بتاريخ 15/12/2026 في فندق الريتز الرياض",
         name="ملتقى الاعمال", date="15/12/2026", place="فندق الريتز الرياض"),
    case("portfolio", "ملف شخصي لمصمم باسم يزن ومهاراتي تصميم شعارات وهوية وايميلي yazan@mail.com",
         name="يزن", services=["تصميم شعارات", "هوية"], email="yazan@mail.com"),
    case("dashboard", "لوحة بيانات باسم الزيارات فيها الاثنين 22 الثلاثاء 31", name="الزيارات", data_labels=["الاثنين", "الثلاثاء"]),
    case("ask", "ابغى موقع لمغسلة جوالي 0501234567"),
    case("refuse", "ابغى موقع فيه نظام نقاط ومكافآت"),
    case("refuse", "ابغى مدونة فيها بحث متقدم"),
]
