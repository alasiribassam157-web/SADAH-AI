"""Held-out requests (v27), written after v26 was promoted: a different mix from the earlier sets (workshops, clinics, kids, numbers written in
words, a request that opens with a greeting, a refusal for a payment gateway, a style word placed first). NOT MEASURED YET: measure once, record the
number here, promote into tests/builder_cases_h.py (or a new part), write v28.
Earlier sets (all promoted after measuring): v1 15/20, v2 16/20, v3 14/16, v4 10/10, v5 19/20, v6 13/14, v7 16/17, v8 13/16, v9 8/15,
v10 9/14, v11 10/15, v12 10/13, v13 11/13, v14 12/13, v15 13/14, v16 10/11, v17 5/11, v18 9/12, v19 20/30 (from web research on what people
ask for), v20 15/15, v21 12/14, v22 12/14, v23 25/30 (from research on how people write Arabic online), v24 10/12, v25 7/10, v26 10/10; phrasing mine.
Never tune the rules on a case here without first moving it into SUITE and writing a fresh held-out set."""
from tests.builder_requests import case

HELDOUT = [
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
