"""SADAH v4 benchmark additions: prayer times, translation, sports, dialects, typos, more skills (84)."""

CASES_V4 = [
    # --- prayer times (11)
    ("مواقيت الصلاة في الرياض", "prayer", "🕌"), ("متى أذان المغرب في جدة", "prayer", "المطلوبة"),
    ("prayer times in Cairo", "prayer", "🕌"), ("وقت صلاة الفجر في دبي", "prayer", "🕌"), ("مواقيت الصلاة اليوم", "prayer", "🕌"),
    ("متى صلاة العصر في المدينة", "prayer", "🕌"), ("fajr time in London", "prayer", "🕌"), ("when is maghrib in Istanbul", "prayer", "🕌"),
    ("شو مواعيد الصلاة في عمان", "prayer", "🕌"), ("متى العشاء في الكويت", "prayer", "🕌"), ("مواقيت الصلاه في الدمام", "prayer", "🕌"),
    # --- translation (13)
    ("ترجم قطة للانجليزي", "translate", "cat"), ("وش معنى coffee بالعربي", "translate", "قهوة"),
    ("how do you say water in arabic", "translate", "ماء"), ("صقر بالانجليزي", "translate", "falcon"),
    ("ترجم good morning", "translate", "صباح الخير"), ("translate الذكاء الاصطناعي", "translate", "artificial intelligence"),
    ("ترجم برج خليفة للانجليزي", "translate", "Burj Khalifa"), ("what is computer in arabic", "translate", "حاسوب"),
    ("translate photosynthesis to arabic", "translate", "ضوئي"), ("شو يعني friend بالعربي", "translate", "صديق"),
    ("يعني ايه book بالعربي", "translate", "كتاب"), ("كيف اقول مدرسة بالانجليزي", "translate", "school"),
    ("ترجم قطه", "translate", "cat"),
    # --- sports (12)
    ("من مدرب ريال مدريد", "web", "مدرب"), ("ملعب نادي الهلال", "web", "الملك فهد"), ("في اي دوري يلعب الهلال", "web", "الدوري السعودي"),
    ("في اي نادي يلعب كريستيانو رونالدو", "web", "يلعب حالياً"), ("وش مركز ليونيل ميسي", "web", "مركز"),
    ("who is the coach of Manchester City", "web", "head coach"), ("which team does Lionel Messi play for", "web", "plays for"),
    ("stadium of FC Barcelona", "web", "Camp Nou"), ("متى تأسس نادي الاتحاد", "web", "1927"), ("who founded Real Madrid", "web", "founded by"),
    ("what league is Liverpool in", "web", "Premier League"), ("من هو محمد صلاح", "web", "صلاح"),
    # --- Levantine / Egyptian dialects (16)
    ("شو هي عاصمة اليابان", "web", "طوكيو"), ("قديش عدد سكان مصر", "web", "نسمة"), ("مين هو المتنبي", "web", "المتنبي"),
    ("ازاي اعكس نص في بايثون", "code", "[::-1]"), ("الساعة كام", "datetime", "🕐"), ("الجو عامل ايه في القاهرة", "weather", "°"),
    ("بكام 100 دولار بالجنيه المصري", "currency", "جنيه مصري"), ("قديش 15 ضرب 4", "python", "60"),
    ("عايز اعرف عن الأهرامات", "web", "هرم"), ("شو يعني الذكاء الاصطناعي", "web", "ذكاء"), ("ازيك", "chat", ""),
    ("يسلمو", "chat", ""), ("فين يقع برج إيفل", "web", "إيفل"), ("امتى اتأسست السعودية", "web", "تأسست"),
    ("مين اخترع المصباح الكهربائي", "web", "إديسون"), ("بدي كود حلقة for بجافا", "code", "for (int"),
    # --- typos (10)
    ("وش الطقص في جدة", "weather", "°"), ("ما هي عاصمه اليابان", "web", "طوكيو"), ("how is the wether in London", "weather", "°"),
    ("calculte 25 * 4", "python", "100"), ("convrt 10 km to miles", "units", "6.2137"), ("pyhton for loop", "code", "range"),
    ("كيف اعكس نص في بايثن", "code", "[::-1]"), ("الساعه كم", "datetime", "🕐"), ("مواقيت الصلاة في مكه", "prayer", "🕌"),
    ("كم عدد سكان الكويت؟؟", "web", "نسمة"),
    # --- more facts and length control (7)
    ("كم مساحة مصر", "web", "كم²"), ("where was Steve Jobs born", "web", "San Francisco"), ("how tall is Burj Khalifa", "web", "828"),
    ("من مؤسس أبل", "web", "ستيف"), ("official language of Brazil", "web", "Portuguese"), ("اشرح المريخ بالتفصيل", "web", "المريخ"),
    ("ما هو التركيب الضوئي باختصار", "web", "ضوئي"),
    # --- units, currency, code and math variety (15)
    ("convert 1 TB to GB", "units", "1,024"), ("كم ميل في 42 كيلومتر", "units", "26.0976"), ("حول 25 مئوية الى فهرنهايت", "units", "77"),
    ("1 inch to cm", "units", "2.54"), ("كم 500 ريال بالدولار", "currency", "="), ("100 درهم كم ريال", "currency", "درهم"),
    ("convert 200 EUR to GBP", "currency", "="), ("how to use try catch in c#", "code", "catch"), ("random number in go", "code", "rand.Intn"),
    ("json in python", "code", "json.loads"), ("hello world in go", "code", "fmt.Println"), ("sort an array in java", "code", "Arrays.sort"),
    ("وش ناتج 9 ضرب 9", "python", "81"), ("what is 12% of 50", "python", "6"), ("calculate 1000 / 8", "python", "125"),
]
