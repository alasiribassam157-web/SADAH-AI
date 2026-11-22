"""The builder's Arabic request suite: 30 requests, each with what the builder must do.

skill   landing / dashboard / shop / webapp : build a site of that kind that passes every static check,
                                              and match `expect` (spec attributes: name, business, accent, app,
                                              sections (subset), data_labels, items_n)
        ask    : build nothing and ask the one short question
        refuse : build nothing and say plainly it is not supported
"""


def case(skill: str, q: str, **expect) -> dict:
    return {"skill": skill, "q": q, "expect": expect}


SUITE = [
    case("landing", "أبغى موقع لمعرض سيارات باسم النخبة وفيه صفحة اتصال", name="النخبة", business="معرض سيارات", sections=["contact"]),
    case("landing", "سوّ لي موقع تعريفي لمطعم اسمه بيت الشواء ولونه أحمر", name="بيت الشواء", business="مطعم", accent="#b91c1c"),
    case("landing", "ابغى موقع لمقهى باسم ركن القهوة فيه قسم الأسعار", name="ركن القهوة", business="مقهى", sections=["pricing"]),
    case("landing", "موقع لعيادة أسنان اسمها ابتسامة باللون الأخضر", name="ابتسامة", business="عيادة", accent="#15803d"),
    case("landing", "صمم موقع لمكتب محاماة اسمه العدل وفيه آراء العملاء", name="العدل", business="مكتب محاماة", sections=["testimonials"]),
    case("landing", "موقع لمتجر ملابس باسم أناقة وفيه معرض صور", name="أناقة", business="متجر ملابس", sections=["gallery"]),
    case("landing", "أبي موقع لشركة برمجة اسمها سحابة ولونه بنفسجي", name="سحابة", business="شركة تقنية", accent="#6d28d9"),
    case("landing", "موقع لصالون حلاقة باسم لمسة وفيه أسعار وباقات", name="لمسة", business="صالون", sections=["pricing"]),
    case("landing", "موقع لمدرسة اسمها المستقبل فيه من نحن وتواصل", name="المستقبل", business="جهة تعليمية", sections=["about", "contact"]),
    case("landing", "موقع لمكتب عقارات باسم الديار ولونه ذهبي", name="الديار", business="مكتب عقارات", accent="#a16207"),
    case("dashboard", "لوحة بيانات باسم مبيعات الشركة فيها يناير 100 فبراير 150 مارس 90", name="مبيعات الشركة", data_labels=["يناير", "فبراير", "مارس"]),
    case("dashboard", "أبغى لوحة بيانات باسم المصاريف مصروف 500 إيجار 2000 كهرباء 300", name="المصاريف", data_labels=["مصروف", "إيجار", "كهرباء"]),
    case("dashboard", "سوّ لي لوحة باسم الزوار ولونها أخضر وفيها السبت 40 الأحد 55", name="الزوار", accent="#15803d", data_labels=["السبت", "الأحد"]),
    case("dashboard", "لوحة بيانات باسم الأداء", name="الأداء", data_labels=[]),
    case("dashboard", "لوحة بيانات باسم الحضور فيها حاضر ٨٠ غائب ٢٠", name="الحضور", data_labels=["حاضر", "غائب"]),
    case("shop", "سوّ لي متجر باسم الورد وفيه ورد 20 وشموع 35 وعطر 120", name="الورد", items_n=3),
    case("shop", "أبغى متجر باسم البن وفيه قهوة 45 وهيل 60", name="البن", items_n=2),
    case("shop", "متجر إلكتروني باسم أناقة لبيع الملابس", name="أناقة", items_n=0),
    case("shop", "أبي منتجات للعرض باسم الحرفيون ولونه برتقالي", name="الحرفيون", accent="#c2410c"),
    case("shop", "متجر باسم الكتب وفيه رواية 30 وقصة 25 وشعر 40 ولونه بنفسجي", name="الكتب", items_n=3, accent="#6d28d9"),
    case("webapp", "أبغى تطبيق قائمة مهام باسم مهامي ولونه أخضر", name="مهامي", app="tasks", accent="#15803d"),
    case("webapp", "تطبيق نموذج تسجيل باسم دورة البرمجة", name="دورة البرمجة", app="register"),
    case("webapp", "أبي تطبيق مهام باسم يومي", name="يومي", app="tasks"),
    case("webapp", "سوّ لي تطبيق اشتراك باسم النشرة", name="النشرة", app="register"),
    case("ask", "سوّ لي موقع لمطعم وفيه صفحة اتصال"),
    case("ask", "أبغى موقع لمعرض سيارات"),
    case("ask", "أبغى لوحة بيانات لمبيعاتي"),
    case("refuse", "أبغى تطبيق لحجز المواعيد"),
    case("refuse", "أبغى تطبيق جوال للتوصيل"),
    case("refuse", "سوّ لي موقع فيه بوابة دفع"),
    # moved from held-out v1 after measuring it (15/20 before tuning, see tests/builder_heldout.py)

    case("landing", "ودي أسوي موقع لمحل حلويات اسمه سكر وفيه تواصل", name="سكر"),
    case("landing", "عندي صالون نسائي وابغى له موقع باسم رونق", name="رونق", business="صالون"),
    case("ask", "اعملي صفحة تعريفية لعيادة اسنان الابتسامة الذهبية"),  # no explicit name: ask, never guess
    case("landing", "أبغى موقع لشركة تطبيقات اسمها نبض ولونه أزرق", name="نبض", accent="#1d4ed8"),
    case("landing", "موقع بسيط لمكتبي القانوني باسم الحق وأبغى فيه نبذة وخدمات", name="الحق", business="مكتب محاماة"),
    case("landing", "صمملي موقع لورشة سيارات اسمها المحرك", name="المحرك"),
    case("landing", "ابغى موقع لمطعم برجر باسم برجرنا ولونه اسود", name="برجرنا", accent="#111827"),
    case("landing", "أبي موقع لمقهى باسم \"ظل\" وفيه أسعار", name="ظل", sections=["pricing"]),
    case("landing", "ابغى موقع لعيادة باسم شفاء ولون الموقع احمر", name="شفاء", accent="#b91c1c"),
    case("dashboard", "أبغى لوحة تعرض مبيعات الاسبوع باسم أسبوعي السبت ١٠٠ الأحد ١٢٠ الاثنين ٩٠", name="أسبوعي", data_labels=["السبت", "الأحد", "الاثنين"]),
    case("dashboard", "ابغى داشبورد باسم المصروفات", name="المصروفات"),
    case("shop", "ابغى اسوي متجر لبيع العطور واسمه عبير وفيه عود 300 ومسك 150", name="عبير", items_n=2),
    case("shop", "متجر صغير باسم زهرة فيه ورد ٢٥ وفل ١٥", name="زهرة", items_n=2),
    case("webapp", "أبي تطبيق بسيط أكتب فيه مهامي باسم تذكير", name="تذكير", app="tasks"),
    case("webapp", "نموذج تسجيل للمشتركين باسم ملتقى", name="ملتقى", app="register"),
    case("ask", "ابغى موقع"),
    case("refuse", "اعملي متجر مع بوابة دفع مدى"),
    case("refuse", "ابغى تطبيق اندرويد باسم رحلة"),
    case("refuse", "سوّ لي موقع فيه تسجيل دخول للأعضاء"),
    case("refuse", "ابغى تطبيق يتذكر مواعيدي"),
    # moved from held-out v2 after measuring it (16/20 before tuning)

    case("landing", "ابغى موقع لنادي رياضي باسم القوة وفيه اسعار", name="القوة", sections=["pricing"]),
    case("landing", "موقع تعريفي لمزرعة اسمها الواحة ولونه اخضر", name="الواحة", accent="#15803d"),
    case("landing", "ابي موقع لشركة عقارات باسم بيتك وفيه صور", name="بيتك", business="مكتب عقارات", sections=["gallery"]),
    case("landing", "اعمل لي موقع لمكتب هندسي باسم البناء", name="البناء"),
    case("landing", "موقع لمحل جوالات اسمه تقنية الجوال", name="تقنية الجوال"),
    case("landing", "أبغى موقع لحلاق باسم الأناقة الرجالية ولونه ذهبي", name="الأناقة الرجالية", accent="#a16207"),
    case("landing", "ابغى موقع لمدرسة تحفيظ باسم النور وفيه من نحن", name="النور", sections=["about"]),
    case("landing", "موقع لمطعم مأكولات بحرية باسم الصياد وفيه معرض صور وأسعار", name="الصياد", sections=["gallery", "pricing"]),
    case("dashboard", "لوحة بيانات باسم الحضور الشهري فيها يناير ٥٠ فبراير ٦٠ مارس ٧٥", name="الحضور الشهري", data_labels=["يناير", "فبراير", "مارس"]),
    case("dashboard", "ابغى لوحه للمبيعات باسم متابعة", name="متابعة"),
    case("dashboard", "لوحة بيانات باسم التبرعات فيها الاسبوع الاول 300 الاسبوع الثاني 450", name="التبرعات", data_labels=["الاسبوع الاول", "الاسبوع الثاني"]),
    case("shop", "متجر باسم تمور القصيم وفيه سكري 40 وخلاص 35", name="تمور القصيم", items_n=2),
    case("shop", "ابي اعرض منتجاتي في موقع باسم حرفة", name="حرفة"),
    case("shop", "ابغى متجر باسم الدانة ولونه احمر وفيه عباية 250 وشال 90", name="الدانة", accent="#b91c1c", items_n=2),
    case("webapp", "ابغى تطبيق يسجل المهام باسم انجاز", name="انجاز", app="tasks"),
    case("webapp", "تطبيق صغير نموذج اشتراك باسم نشرتي", name="نشرتي", app="register"),
    case("ask", "ابغى لوحة بيانات"),
    case("refuse", "ابغى موقع فيه سلة مشتريات ودفع"),
    case("refuse", "ابغى تطبيق ايفون باسم سفر"),
    case("refuse", "سوّ لي موقع ذكاء اصطناعي يجاوب الزوار"),
    # moved from held-out v3 after measuring it (14/16 before tuning)

    case("landing", "ابغى موقع لمكتب سياحة باسم رحلاتنا وفيه خدماتنا وتواصل", name="رحلاتنا", sections=["services", "contact"]),
    case("landing", "سو لي موقع لمعهد لغات اسمه لسان ولونه ازرق", name="لسان", accent="#1d4ed8"),
    case("landing", "ودي بموقع لعيادة بيطرية باسم رفق", name="رفق"),
    case("landing", "موقع شخصي لي باسم محمد العتيبي فيه من نحن وصور", name="محمد العتيبي", sections=["about", "gallery"]),
    case("landing", "أبغى موقع لشركة نقل اسمها السريع ولون الموقع اخضر", name="السريع", accent="#15803d"),
    case("landing", "عاوز موقع لمخبز اسمه فرن البلد", name="فرن البلد"),
    case("dashboard", "لوحة بيانات باسم الرحلات فيها السبت 12 الاحد 18 الاثنين 7 الثلاثاء 22", name="الرحلات", data_labels=["السبت", "الاحد", "الاثنين", "الثلاثاء"]),
    case("dashboard", "ابغى داشبورد للحضور باسم دوام موظف 30 مدير 5", name="دوام", data_labels=["موظف", "مدير"]),
    case("shop", "متجر باسم عبق وفيه بخور 50 ودهن عود 200 ومعطر 35", name="عبق", items_n=3),
    case("shop", "اعرض منتجاتي: شنطة 150 وحذاء 220 باسم خطوة", name="خطوة"),
    case("webapp", "ابي تطبيق لتنظيم مهامي باسم ترتيب", name="ترتيب", app="tasks"),
    case("webapp", "نموذج تسجيل لحضور الفعالية باسم لقاء", name="لقاء", app="register"),
    case("ask", "ابغى متجر"),
    case("refuse", "ابغى موقع باسم تواصل فيه دردشة مباشرة مع الزوار"),
    case("refuse", "ابغى تطبيق ويندوز باسم حاسب"),
    case("refuse", "ابغى موقع باسم حوالات يرسل اموال للناس"),
]
SKILLS = ["landing", "dashboard", "shop", "webapp", "ask", "refuse"]
