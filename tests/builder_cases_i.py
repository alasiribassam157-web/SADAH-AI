"""Builder requests, part I: held-out v27 (10/10 measured once before any tuning; like v26 it says little, because I wrote it knowing
the rules: a set the rules already handle cannot find new weaknesses)."""
from tests.builder_case import case

CASES = [
    case("landing", "السلام عليكم ابغى موقع لورشة نجارة باسم خشبنا", name="خشبنا"),
    case("shop", "متجر حلويات باسم سكر فيه كنافة 25 ولقيمات 15 وبسبوسة 20", name="سكر", items_n=3),
    case("game", "لعبة اسئلة عن الفضاء باسم مجرة", name="مجرة", game="quiz"),
    case("webapp", "تطبيق عداد للتسبيح باسم ذكر", name="ذكر", app="counter"),
    case("blog", "مدونة عن السفر باسم رحال", name="رحال"),
    case("event", "دعوة لتخرج باسم سارة الساعة 7 مساء في جامعة الملك سعود", name="سارة", time="7 مساء"),
    case("landing", "فخم موقع لمجوهرات باسم درة", name="درة", theme="luxe"),
    case("dashboard", "لوحة للمصاريف باسم ميزانيتي الايجار 3000 الكهرباء 400", name="ميزانيتي", data_labels=["الايجار", "الكهرباء"]),
    case("webapp", "ابي تطبيق مؤقت للمذاكرة باسم تركيز", name="تركيز", app="timer"),
    case("refuse", "ابغى موقع فيه بوابة دفع ببطاقات الائتمان"),
]
