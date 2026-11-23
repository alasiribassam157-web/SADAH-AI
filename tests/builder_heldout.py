"""Held-out requests (v16), written before looking at how the rules treat them (more Gulf phrasings of games, a game next to
other features, sites that only mention games). NOT MEASURED YET: measure once, record the number here, promote into
tests/builder_cases_e.py and write v17.
Earlier sets (all promoted after measuring): v1 15/20, v2 16/20, v3 14/16, v4 10/10, v5 19/20, v6 13/14, v7 16/17,
v8 13/16, v9 8/15, v10 9/14, v11 10/15, v12 10/13, v13 11/13, v14 12/13, v15 13/14.
Never tune the rules on a case here without first moving it into SUITE and writing a fresh held-out set."""
from tests.builder_requests import case

HELDOUT = [
    case("game", "ابغى لعبة بسيطة للجوال اطابق فيها الصور باسم تطابق", name="تطابق", game="memory"),
    case("game", "ابي لعبة اسئلة دينية وثقافية باسم اختبر نفسك", name="اختبر نفسك", game="quiz"),
    case("game", "لعبة تخمين الارقام ولونها اسود", game="guess", accent="#111827"),
    case("game", "ابغى لعبة ثعبان كلاسيكية ولونها برتقالي باسم سلك", name="سلك", game="snake", accent="#c2410c"),
    case("game", "العب اكس او مع الكمبيوتر", game="xo"),
    case("landing", "موقع لمركز تدريب باسم مهارات فيه قسم عن الالعاب التعليمية", name="مهارات"),
    case("shop", "متجر الكتروني باسم هواة وفيه لعبة بزل 60 وشطرنج 90", name="هواة", items_n=2),
    case("ask", "ابغى لعبة ممتعة"),
    case("refuse", "ابغى لعبة ثلاثية الابعاد"),
    case("blog", "مدونة باسم عالم الالعاب", name="عالم الالعاب"),
    case("event", "دعوة لبطولة العاب باسم كاس المحترفين يوم السبت", name="كاس المحترفين", date="السبت"),
]
