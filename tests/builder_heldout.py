"""Held-out requests (v22), written after v21 was promoted: fresh domains and phrasings (a business described in the first person,
skin care, specialty coffee, a currency converter that needs live rates, a quiz for children) and a few looks in new words.
NOT MEASURED YET: measure once, record the number here, promote into tests/builder_cases_e.py, write v23.
Earlier sets (all promoted after measuring): v1 15/20, v2 16/20, v3 14/16, v4 10/10, v5 19/20, v6 13/14, v7 16/17, v8 13/16, v9 8/15,
v10 9/14, v11 10/15, v12 10/13, v13 11/13, v14 12/13, v15 13/14, v16 10/11, v17 5/11, v18 9/12, v19 20/30 (written from web research on
what people ask for; the phrasing is mine, not real users), v20 15/15, v21 12/14.
Never tune the rules on a case here without first moving it into SUITE and writing a fresh held-out set."""
from tests.builder_requests import case

HELDOUT = [
    case("landing", "عندي مكتب سياحة وابي موقع له باسم وجهتك", name="وجهتك"),
    case("landing", "ابي صفحة تعريفية لحضانة باسم نمو", name="نمو"),
    case("shop", "ابغى اعرض منتجات العناية بالبشرة باسم نضارة فيها كريم 90 وغسول 60", name="نضارة", items_n=2),
    case("shop", "متجر قهوة مختصة باسم حبة وفيه اثيوبي 70 وكولومبي 65", name="حبة", items_n=2),
    case("portfolio", "ابغى بورتفوليو لمطور تطبيقات باسم رامي ومهاراتي فلاتر وفايربيس", name="رامي"),
    case("blog", "مدونة عن الاستثمار باسم محفظتي", name="محفظتي"),
    case("event", "دعوة لحفل تكريم باسم تكريم المتفوقين يوم الاثنين الساعة 6 مساء في القاعة الكبرى", name="تكريم المتفوقين", date="الاثنين", time="6 مساء"),
    case("dashboard", "لوحة بيانات باسم المبيعات الاسبوعية السبت 50 الاحد 65 الاثنين 40", name="المبيعات الاسبوعية", data_labels=["السبت", "الاحد", "الاثنين"]),
    case("webapp", "ابي حاسبة باسم حساب سريع", name="حساب سريع", app="calculator"),
    case("refuse", "ابغى تطبيق يحول العملات باسم صرف"),
    case("game", "لعبة اسئلة جغرافيا للاطفال باسم رحلة", name="رحلة", game="quiz", topic="geography"),
    case("game", "ابغى لعبة ذاكرة بثيم داكن", game="memory", theme="dark"),
    case("ask", "ابغى تطبيق مؤقت"),
    case("refuse", "ابي موقع فيه اشعارات للعملاء"),
]
