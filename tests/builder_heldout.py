"""Held-out requests (v14), written before looking at how the rules treat them (fresh trades, Gulf spellings,
requests that mention a feature only in passing, several facts at once). NOT MEASURED YET: measure once, record
the number here, promote into tests/builder_cases_d.py and write v15.
Earlier sets (all promoted after measuring): v1 15/20, v2 16/20, v3 14/16, v4 10/10, v5 19/20, v6 13/14, v7 16/17,
v8 13/16, v9 8/15, v10 9/14 (a two-word dashboard label stays a known limit), v11 10/15, v12 10/13, v13 11/13.
Never tune the rules on a case here without first moving it into SUITE and writing a fresh held-out set."""
from tests.builder_requests import case

HELDOUT = [
    case("landing", "ابغى موقع لمعهد لغات باسم لسان وخدماتنا انجليزي وفرنسي وجوالي 0571234567", name="لسان",
         services=["انجليزي", "فرنسي"], phone="0571234567"),
    case("landing", "موقع لمحل نظارات باسم رؤية في جدة ودوامنا من 4 عصرا الى 11 ليلا", name="رؤية", city="جدة",
         hours="من 4 عصرا الى 11 ليلا"),
    case("landing", "موقع لمزرعة باسم الواحة ولونه اخضر", name="الواحة", accent="#15803d", business="مزرعة"),
    case("shop", "ابغى متجر باسم حلا وفيه كيكة 120 وكوكيز 40", name="حلا", items_n=2),
    case("dashboard", "لوحة بيانات باسم الحضور الاحد 30 الاثنين 28 الثلاثاء 35", name="الحضور", data_labels=["الاحد", "الاثنين", "الثلاثاء"]),
    case("blog", "ابي مدونة باسم رحلات صغيرة وفيها قسم عن الكاتب", name="رحلات صغيرة"),
    case("portfolio", "ملف اعمال باسم م. ريم ومهاراتي هندسة وتصميم داخلي", name="م. ريم", services=["هندسة", "تصميم داخلي"]),
    case("event", "دعوة لمؤتمر باسم مستقبل التقنية يوم الاحد الساعة 10 صباحا في فندق الريتز", name="مستقبل التقنية", date="الاحد",
         time="10 صباحا"),
    case("webapp", "تطبيق مهام باسم اولوياتي", name="اولوياتي", app="tasks"),
    case("ask", "ابي موقع لمكتبة"),
    case("refuse", "ابغى موقع فيه نظام تذاكر دعم"),
    case("refuse", "ابغى موقع فيه صفحة لكل موظف مع تسجيل دخول"),
    case("refuse", "ابغى متجر ببوابة دفع الكترونية"),
]
