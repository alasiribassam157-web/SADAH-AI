"""Held-out requests (v6) for the builder, written before looking at how the rules treat them.
The rules in builder/understand.py are tuned on tests/builder_requests.py only. Measure once, then record the
number and promote these cases into SUITE. Earlier sets (all promoted after measuring):
  v1 15/20, v2 16/20, v3 14/16, v4 10/10, v5 19/20.
One v6 case ('دفعة' = a graduating class) was seen refused as 'دفع' (payment) on the live preview, so it moved to SUITE
and was replaced here.
Never tune the rules on a case here without first moving it into SUITE and writing a fresh held-out set."""
from tests.builder_requests import case

HELDOUT = [
    case("portfolio", "ابغى موقع لعرض اعمالي كمصمم جرافيك باسم بصمة", name="بصمة"),
    case("portfolio", "ملف شخصي لطبيبة اسمه د. هند", name="د. هند"),
    case("blog", "ابغى مدونة عن الكتب باسم صفحات ولونها بنفسجي", name="صفحات", accent="#6d28d9"),
    case("blog", "موقع لكتابة مقالاتي الرياضية اسمه ملعب", name="ملعب"),
    case("event", "ابغى دعوة لحفل تخرج 2026 باسم اصدقاء الجامعة", name="اصدقاء الجامعة"),
    case("event", "صفحة لمناسبة عيد ميلاد باسم يوم سعيد ولونها برتقالي", name="يوم سعيد", accent="#c2410c"),
    case("event", "موقع لملتقى رواد الاعمال باسم رواد", name="رواد"),
    case("landing", "موقع لمركز تدريب باسم مهارة وفيه خدماتنا واسعار", name="مهارة", sections=["services", "pricing"]),
    case("landing", "ابغى موقع لمزرعة ابل باسم الصحراء ولونه ذهبي", name="الصحراء", accent="#a16207"),
    case("dashboard", "لوحة بيانات باسم المخزون فيها سكر 30 ارز 45 شاي 12", name="المخزون", data_labels=["سكر", "ارز", "شاي"]),
    case("shop", "متجر باسم صنع بيدي وفيه صابون 15 وشموع 25", name="صنع بيدي", items_n=2),
    case("webapp", "ابغى تطبيق نموذج تسجيل باسم ورشة التصوير", name="ورشة التصوير", app="register"),
    case("ask", "ابغى موقع لمؤتمر"),
    case("refuse", "ابغى مدونة فيها دفع للاشتراك"),
]
