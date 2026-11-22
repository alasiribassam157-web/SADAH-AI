"""Development suite for builder/edit.py: the rules were tuned on these cases, so passing them is NOT evidence of
quality (tests/builder_edit_heldout.py is). Cases promoted from a measured held-out set are marked E1, E2, …"""
LANDING = "موقع لمطعم باسم بيت الشواء"
SHOP = "متجر باسم الورد وفيه ورد 20 وشموع 35"
DASH = "لوحة بيانات باسم المبيعات فيها يناير 100 فبراير 150"
CLINIC = "موقع لعيادة اسنان باسم ابتسامة"
PERFUME = "متجر باسم عطور الشرق وفيه عود 300 ومسك 150 وبخور 50"
ORDERS = "لوحة بيانات باسم الطلبات السبت 12 الاحد 18 الاثنين 9"

E1 = [  # promoted: first measurement 14/16, both failures fixed at the cause (verbs were not normalised; a refusal counted as a change)
    (LANDING, "خلي اللون اخضر", {"changed": True, "accent": "#15803d"}),
    (LANDING, "غير اللون الى البنفسجي", {"changed": True, "accent": "#6d28d9"}),
    (LANDING, "اضف قسم الاسعار", {"changed": True, "sections_has": ["pricing"]}),
    (LANDING, "ابغى قسم الصور", {"changed": True, "sections_has": ["gallery"]}),
    (LANDING, "شيل قسم من نحن", {"changed": True, "sections_not": ["about"]}),
    (LANDING, "اضف خدمة تغليف", {"changed": True, "services_has": ["تغليف"]}),
    (LANDING, "غير الاسم الى مطعم النخبة", {"changed": True, "name": "مطعم النخبة"}),
    (LANDING, "جوالي 0501234567 وايميلي a@b.com", {"changed": True, "phone": "0501234567", "email": "a@b.com"}),
    (LANDING, "نعمل من 9 صباحا الى 11 مساء", {"changed": True, "hours": "من 9 صباحا الى 11 مساء"}),
    (SHOP, "اضف منتج عطر 120", {"changed": True, "items_has": [("عطر", "120 ريال")]}),
    (SHOP, "احذف منتج شموع", {"changed": True, "items_not": ["شموع"]}),
    (DASH, "اضف مارس 90", {"changed": True, "data_has": [("مارس", 90.0)]}),
    ("دعوة لحفل باسم لقاء", "يوم الخميس الساعة 8 مساء في قاعة الماسة",
     {"changed": True, "date": "الخميس", "time": "8 مساء", "place": "قاعة الماسة"}),
    (LANDING, "اضف سلة مشتريات", {"changed": False, "note_has": "غير مدعوم"}),
    (LANDING, "هههههه", {"changed": False, "note_has": "ما فهمت"}),
    (LANDING, "احذف قسم التواصل", {"changed": False, "note_has": "التواصل"}),
]

E2 = [  # promoted: first measurement 13/16; fixed at the cause (item names were read as feature requests; «مدينتنا»; «ومنتج» glued to a name)
    (LANDING, "ابي اللون اسود", {"changed": True, "accent": "#111827"}),
    (LANDING, "حط لون ازرق", {"changed": False}),   # already blue
    (LANDING, "غيّر لونه إلى الأحمر", {"changed": True, "accent": "#b91c1c"}),
    (LANDING, "زود قسم الباقات", {"changed": True, "sections_has": ["pricing"]}),
    (LANDING, "امسح قسم الخدمات", {"changed": True, "sections_not": ["services"]}),
    (LANDING, "اضف خدمة حجز طاولات", {"changed": True, "services_has": ["حجز طاولات"]}),
    (LANDING, "خلي اسم الموقع شواء الديرة", {"changed": True, "name": "شواء الديرة"}),
    (LANDING, "رقمي 0555123456", {"changed": True, "phone": "0555123456"}),
    (LANDING, "مدينتنا الدمام", {"changed": True, "city": "الدمام"}),
    (SHOP, "ضيف منتج عود 300 ومنتج مسك 150", {"changed": True, "items_has": [("عود", "300 ريال"), ("مسك", "150 ريال")]}),
    (SHOP, "شيل منتج ورد", {"changed": True, "items_not": ["ورد"]}),
    ("لوحة بيانات باسم الزوار الاحد 5 الاثنين 8 الثلاثاء 3", "احذف الاثنين", {"changed": True}),
    (LANDING, "اضف نظام نقاط", {"changed": False, "note_has": "غير مدعوم"}),
    (LANDING, "ممكن تساعدني", {"changed": False, "note_has": "ما فهمت"}),
    ("ملف شخصي باسم سارة", "اضف مهارة تصميم", {"changed": True, "services_has": ["تصميم"]}),
    ("تطبيق نموذج تسجيل باسم دورتي", "غير اللون الى الاخضر", {"changed": True, "accent": "#15803d"}),
]

E3 = [  # promoted: first measurement 12/16; fixed at the cause (colour without «لون», «نبي», «الاسم الجديد», product names after a kind word, several sections in one sentence)
    (CLINIC, "خله بنفسجي", {"changed": True, "accent": "#6d28d9"}),
    (CLINIC, "نبي اللون الذهبي", {"changed": True, "accent": "#a16207"}),
    (CLINIC, "نبي قسم الصور وقسم آراء العملاء", {"changed": True, "sections_has": ["gallery", "testimonials"]}),
    (CLINIC, "ابغى اشيل قسم نبذة", {"changed": True, "sections_not": ["about"]}),
    (CLINIC, "اضف خدمة تبييض الاسنان", {"changed": True, "services_has": ["تبييض الاسنان"]}),
    (CLINIC, "الاسم الجديد ابتسامة الغد", {"changed": True, "name": "ابتسامة الغد"}),
    (CLINIC, "ايميلنا info@clinic.sa", {"changed": True, "email": "info@clinic.sa"}),
    (CLINIC, "نفتح من الساعة 4 مساء الى 10 مساء", {"changed": True, "hours": "من الساعة 4 مساء الى 10 مساء"}),
    (PERFUME, "اضف منتج ماء ورد 40", {"changed": True, "items_has": [("ماء ورد", "40 ريال")]}),
    (PERFUME, "احذف مسك", {"changed": True, "items_not": ["مسك"]}),
    (ORDERS, "اضف الثلاثاء 15", {"changed": True, "data_has": [("الثلاثاء", 15.0)]}),
    (CLINIC, "اضف تقييمات العملاء", {"changed": False, "note_has": "غير مدعوم"}),
    (CLINIC, "ما اعرف وش اكتب", {"changed": False, "note_has": "ما فهمت"}),
    ("مدونة باسم رحال", "غير الاسم الى رحال الجديد", {"changed": True, "name": "رحال الجديد"}),
    ("دعوة لزفاف باسم سلمى وخالد", "الساعة 9 مساء", {"changed": True, "time": "9 مساء"}),
    (CLINIC, "اضف قسم الاسعار والغ قسم من نحن", {"changed": True, "sections_has": ["pricing"], "sections_not": ["about"]}),
]

DEV = [
    (LANDING, "لونه ذهبي", {"changed": True, "accent": "#a16207"}),
    (LANDING, "بدل اللون الى الاحمر", {"changed": True, "accent": "#b91c1c"}),
    (LANDING, "اللون برتقالي", {"changed": True, "accent": "#c2410c"}),
    (LANDING, "ضيف قسم آراء العملاء", {"changed": True, "sections_has": ["testimonials"]}),
    (LANDING, "بدون قسم الصور", {"changed": False}),   # not there: nothing to remove
    (LANDING, "المدينة جدة", {"changed": True, "city": "جدة"}),
    (LANDING, "غير المدينة الى الرياض", {"changed": True, "city": "الرياض"}),
    (LANDING, "اضف خدمة توصيل وخدمة تغليف", {"changed": True, "services_has": ["توصيل"]}),
    (SHOP, "ضيف منتج بخور 50", {"changed": True, "items_has": [("بخور", "50 ريال")]}),
    (SHOP, "اضف منتج هدية", {"changed": True, "items_has": [("هدية", "")]}),
    (DASH, "احذف فبراير", {"changed": False, "note_has": "نقطتين"}),
    ("لوحة بيانات باسم م يناير 10 فبراير 20 مارس 30", "احذف فبراير", {"changed": True}),
    (DASH, "اضف مارس 90 وابريل 70", {"changed": True, "data_has": [("مارس", 90.0)]}),
    (LANDING, "اضف مدفوعات", {"changed": False}),
    (LANDING, "اضف بث مباشر", {"changed": False, "note_has": "غير مدعوم"}),
    (LANDING, "خلي الاسم مطعم الجود", {"changed": True, "name": "مطعم الجود"}),
    ("تطبيق قائمة مهام باسم مهامي", "اضف قسم الاسعار", {"changed": False}),
]
SUITE = E1 + E2 + E3 + DEV
