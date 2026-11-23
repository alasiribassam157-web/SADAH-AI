"""Builder requests, part K: held-out v29 (10/10 measured once before any tuning, again on a set aimed at suspected weaknesses)."""
from tests.builder_case import case

CASES = [
    case("blog", "ابي مدونة باسم يوميات طالب جامعي", name="يوميات طالب جامعي"),
    case("landing", "موقع لمنصة تعليمية باسم دروسي", name="دروسي"),
    case("shop", "ابغى متجر باسم ركن الشاي فيه اخضر ٣٠ واحمر ٢٥", name="ركن الشاي", items_n=2),
    case("landing", "موقع داكن ولونه ذهبي لمكتب محاماة باسم ميزان", name="ميزان", theme="dark"),
    case("webapp", "تطبيق مصروفات باسم تتبع الانفاق اليومي", name="تتبع الانفاق اليومي", app="expenses"),
    case("game", "لعبة تخمين رقم باسم الغموض", name="الغموض", game="guess"),
    case("dashboard", "لوحة بيانات باسم الزوار فيها الجمعة 70 السبت 95", name="الزوار", data_labels=["الجمعة", "السبت"]),
    case("event", "دعوة لحفل تكريم باسم المعلمين يوم الاحد الساعة 6 مساء", name="المعلمين", time="6 مساء"),
    case("refuse", "اذا ممكن ابي موقع فيه اشتراك مدفوع للاعضاء"),
    case("refuse", "تكرم سو لي موقع فيه تتبع الطلبات للعملاء"),
]
