"""Builder requests, part J: held-out v28 (9/10 before tuning; set aimed at known weaknesses: a three-word name containing a refusal word
was refused, «حسابات الشركة الصغيرة»; one case was a duplicate of the dev suite and was replaced before the number was recorded)."""
from tests.builder_case import case

CASES = [
    case("webapp", "تطبيق ملاحظات باسم حسابات الشركة الصغيرة", name="حسابات الشركة الصغيرة", app="notes"),
    case("landing", "موقع لمعهد لغات باسم لسان وفيه نبذة وخدمات وتواصل", name="لسان"),
    case("blog", "ابغى مدونة عن الرياضة باسم هدف", name="هدف"),
    case("shop", "متجر عطور باسم عبير فيه عود 120 وبخور 60 ودهن 90", name="عبير", items_n=3),
    case("webapp", "تطبيق حاسبة باسم ارقام ذكية", name="ارقام ذكية", app="calculator"),
    case("game", "لعبة اسئلة عن الحيوانات باسم غابة", name="غابة", game="quiz"),
    case("event", "دعوة عقيقة باسم ريم الساعة 5 عصرا في استراحة النخيل", name="ريم", time="5 عصرا"),
    case("portfolio", "ملف اعمال لمصور باسم عدسة", name="عدسة"),
    case("landing", "ابي موقع لشركة شحن باسم نقل سريع", name="نقل سريع"),
    case("refuse", "لو سمحت ابغى موقع فيه توصيل الطلبات وتتبع الشحنة"),
]
