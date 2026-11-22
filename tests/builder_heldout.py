"""Held-out requests (v11) for the builder, written before looking at how the rules treat them (facts inside requests,
names that contain a refused word, hours in unusual wording, unseen unsupported features).
The rules are tuned on tests/builder_requests.py only. Measure once, then record the number and promote.
Earlier sets (all promoted after measuring): v1 15/20, v2 16/20, v3 14/16, v4 10/10, v5 19/20, v6 13/14, v7 16/17,
v8 13/16, v9 8/15, v10 9/14 (a two-word dashboard label stays a known limit).
Never tune the rules on a case here without first moving it into SUITE and writing a fresh held-out set."""
from tests.builder_requests import case

HELDOUT = [
    case("landing", "موقع لمكتب هندسي باسم الاتقان نقدم تصميم ومتابعة تنفيذ وايميلنا contact@itqan.sa",
         name="الاتقان", services=["تصميم", "متابعة تنفيذ"], email="contact@itqan.sa"),
    case("landing", "ابغى موقع لعيادة جلدية باسم نقاء في الدمام جوال 0551234567", name="نقاء", city="الدمام", phone="0551234567"),
    case("landing", "موقع لمحل عطور باسم عود ودوامنا من 4 عصرا الى 12 ليلا", name="عود", hours="من 4 عصرا الى 12 ليلا"),
    case("landing", "ابغى موقع لدار نشر باسم حبر وورق ونبيع كتب ومجلات ودفاتر", name="حبر وورق", services=["كتب", "مجلات", "دفاتر"]),
    case("landing", "ابغى موقع لمركز تجميل باسم لؤلؤة", name="لؤلؤة", services=[]),
    case("shop", "متجر باسم دانة وفيه خاتم ذهب 900 وسوار فضة 350 وجوالي 0561112233", name="دانة", items_n=2, phone="0561112233"),
    case("event", "دعوة لحفل تخرج باسم تخرج سارة بتاريخ 3/6 الساعة 7 مساء في قاعة النخيل",
         name="تخرج سارة", date="3/6", time="7 مساء", place="قاعة النخيل"),
    case("event", "موقع لندوة باسم ندوة الذكاء يوم الاثنين في جامعة الملك سعود", name="ندوة الذكاء", date="الاثنين", place="جامعة الملك سعود"),
    case("portfolio", "ملف اعمال لمصورة باسم هديل في جدة ومهاراتي تصوير منتجات وتصوير مناسبات",
         name="هديل", city="جدة", services=["تصوير منتجات", "تصوير مناسبات"]),
    case("blog", "مدونة باسم وجبة اسبوعية وايميلي hello@wajba.com", name="وجبة اسبوعية", email="hello@wajba.com"),
    case("dashboard", "لوحة بيانات باسم المبيعات فيها الصباح 120 المساء 200 وجوالي 0501234567", name="المبيعات", data_labels=["الصباح", "المساء"]),
    case("webapp", "تطبيق قائمة مهام باسم انجاز جوالي 0501234567", name="انجاز", app="tasks"),
    case("ask", "موقع لمغسلة جوالي 0501234567 ونقدم غسيل"),
    case("refuse", "ابغى موقع فيه حساب لكل عميل"),
    case("refuse", "ابغى متجر فيه توصيل للطلبات"),
]
