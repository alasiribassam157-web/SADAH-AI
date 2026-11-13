"""Benchmark questions for NEXUS-2/3 (146 + 24). NEXUS-4 additions live in benchmark_cases_v4.py."""

# (question, expected intent, text the answer must contain)
CASES_V3 = [
    # --- chat (12)
    ("مرحبا", "chat", "أهلاً"), ("السلام عليكم", "chat", "وعليكم"), ("شكرا لك", "chat", "العفو"), ("كيف حالك", "chat", "بخير"),
    ("صباح الخير", "chat", "صباح النور"), ("من انت", "chat", "سَداة"), ("hello", "chat", "Hi"), ("thanks a lot", "chat", "welcome"),
    ("how are you", "chat", "great"), ("what can you do", "chat", "SADAH"), ("مع السلامة", "chat", "السلامة"), ("good evening", "chat", "evening"),
    # --- facts & encyclopedia (40)
    ("ما هي عاصمة فرنسا؟", "web", "باريس"), ("عاصمة اليابان", "web", "طوكيو"), ("ما هي عاصمة مصر", "web", "القاهرة"),
    ("What is the capital of Japan?", "web", "Tokyo"), ("capital of Germany", "web", "Berlin"), ("capital of Canada", "web", "Ottawa"),
    ("كم عدد سكان مصر", "web", "نسمة"), ("كم عدد سكان الكويت", "web", "نسمة"), ("population of France", "web", "population"),
    ("عملة تركيا", "web", "ليرة"), ("عملة اليابان", "web", "ين"), ("currency of Japan", "web", "yen"), ("currency of the United Kingdom", "web", "pound"),
    ("متى تأسست السعودية", "web", "تأسست"), ("من هو ابن سينا", "web", "ابن سينا"), ("من هو نيوتن", "web", "نيوتن"),
    ("ما هو الذكاء الاصطناعي", "web", "ذكاء"), ("اشرح لي الثقب الأسود", "web", "ثقب"), ("أين يقع برج خليفة", "web", "دبي"),
    ("ما هي الطاقة الشمسية", "web", "شمس"), ("من اخترع المصباح الكهربائي", "web", "إديسون"), ("ما هي لغة بايثون", "web", "بايثون"),
    ("تكلم عن تاريخ القهوة", "web", "القهوة"), ("ما هو فيتامين د", "web", "فيتامين"), ("ما هو المريخ", "web", "المريخ"),
    ("ما هي الخلية", "web", "خلية"), ("من هو المتنبي", "web", "المتنبي"), ("ما هي الأهرامات", "web", "هرم"),
    ("Who was Albert Einstein", "web", "Einstein"), ("explain photosynthesis", "web", "Photosynthesis"), ("what is bitcoin", "web", "Bitcoin"),
    ("how does the internet work", "web", "Internet"), ("tell me about the Roman Empire", "web", "Roman"), ("when did world war 2 end", "web", "World War"),
    ("who painted the Mona Lisa", "web", "Leonardo"), ("Who is Cristiano Ronaldo", "web", "Ronaldo"), ("what is DNA", "web", "DNA"),
    ("where is Mount Everest", "web", "Everest"), ("explain gravity", "web", "Gravity"), ("what is a black hole", "web", "black hole"),
    # --- math (16)
    ("كم يساوي 15 ضرب 7", "python", "105"), ("احسب 2^10", "python", "1024"), ("ما هو الجذر التربيعي لـ 144", "python", "12"),
    ("100 قسمة 4", "python", "25"), ("كم يساوي 12 زائد 30", "python", "42"), ("كم 20٪ من 150", "python", "30"), ("احسب مضروب 6", "python", "720"),
    ("What is 25% of 80", "python", "20"), ("what is 15% of 200", "python", "30"), ("calculate 2 ** 16", "python", "65536"),
    ("what is 7 times 8", "python", "56"), ("square root of 81", "python", "9"), ("calculate (3+4)*5", "python", "35"),
    ("50 minus 8", "python", "42"), ("fibonacci 10", "python", "34"), ("average of 4, 8, 15", "python", "9"),
    # --- code (30)
    ("كيف أعكس نص في بايثون", "code", "[::-1]"), ("how to reverse a string in java", "code", "StringBuilder"),
    ("for loop in javascript", "code", "for (let"), ("how do i write a while loop in go", "code", "for count < 5"),
    ("create a class in c#", "code", "class Person"), ("define a function in c++", "code", "int add"), ("sort a list in python", "code", "sorted("),
    ("كيف أقرأ ملف في جافا", "code", "Files.readString"), ("مثال على قاموس في بايثون", "code", "items()"), ("parse json in javascript", "code", "JSON.parse"),
    ("make an http request in python", "code", "urllib"), ("try catch in java", "code", "catch"), ("random number in javascript", "code", "Math.random"),
    ("how to split a string in go", "code", "strings.Split"), ("hello world in c++", "code", "std::cout"), ("كيف أكتب في ملف بلغة سي شارب", "code", "File.WriteAllText"),
    ("current date in python", "code", "datetime"), ("sum of a list in java", "code", "sum()"), ("how to use a dictionary in c#", "code", "Dictionary"),
    ("if else in python", "code", "elif"), ("declare variables in go", "code", ":="), ("array in javascript", "code", "push"),
    ("كيف أسوي كلاس في بايثون", "code", "__init__"), ("حلقة for في جافا", "code", "for (int"), ("معالجة الاخطاء في بايثون", "code", "except"),
    ("how to read a file in c++", "code", "ifstream"), ("write to a file in go", "code", "os.WriteFile"), ("json in go", "code", "json.Unmarshal"),
    ("how to reverse a string in javascript", "code", "reverse()"), ("sort an array in c++", "code", "std::sort"),
    # --- weather (10)
    ("الطقس في الرياض", "weather", "°"), ("كيف الجو في جدة", "weather", "°"), ("درجة الحرارة في القاهرة", "weather", "°"),
    ("طقس دبي", "weather", "°"), ("weather in London", "weather", "°"), ("what is the weather in Tokyo", "weather", "°"),
    ("temperature in Paris", "weather", "°"), ("هل الجو حار في مكة", "weather", "°"), ("Cairo weather", "weather", "Cairo"), ("حالة الجو اليوم", "weather", "°"),
    # --- currency (10)
    ("كم سعر الدولار", "currency", "="), ("حول 100 دولار الى ريال", "currency", "ريال سعودي"), ("كم 50 يورو بالريال", "currency", "يورو"),
    ("convert 100 USD to EUR", "currency", "euro"), ("how much is 20 pounds in dollars", "currency", "="), ("سعر صرف الدرهم", "currency", "درهم"),
    ("1000 yen in dollars", "currency", "yen"), ("كم 10 دينار كويتي بالريال", "currency", "دينار كويتي"), ("euro to dollar", "currency", "="),
    ("سعر الجنيه المصري مقابل الريال", "currency", "جنيه مصري"),
    # --- date/time (8)
    ("كم الساعة", "datetime", "🕐"), ("ما هو تاريخ اليوم", "datetime", "📅"), ("التاريخ الهجري", "datetime", "📅"), ("وش اليوم", "datetime", "📅"),
    ("what time is it", "datetime", "🕐"), ("what is the date today", "datetime", "📅"), ("hijri date today", "datetime", "📅"), ("الوقت الان", "datetime", "🕐"),
    # --- units (12)
    ("حول 10 كيلومتر الى ميل", "units", "6.2137"), ("convert 5 miles to km", "units", "8.0467"), ("100 fahrenheit to celsius", "units", "37.7778"),
    ("كم قدم في 10 متر", "units", "32.8084"), ("convert 70 kg to pounds", "units", "154.3236"), ("2 gallons in liters", "units", "7.5708"),
    ("حول 1 جيجابايت الى ميجابايت", "units", "1,024"), ("30 celsius to fahrenheit", "units", "86"), ("كم رطل في 5 كيلوجرام", "units", "11.0231"),
    ("convert 12 inches to cm", "units", "30.48"), ("100 km/h to mph", "units", "62.1371"), ("500 grams to kg", "units", "0.5"),
    # --- files (6)
    ("create file bench_note.txt with content benchmark ok", "file", "Created"), ("read bench_note.txt", "file", "benchmark ok"),
    ("list files", "file", "bench_note.txt"), ("انشئ ملف ideas_bench.txt", "file", "Created"), ("اعرض الملفات", "file", "ideas_bench.txt"),
    ("delete file bench_note.txt", "file", "Deleted"),
    # --- NEXUS-3: new facts, answer length, English fallback, Gulf dialect (24)
    ("متى ولد ابن خلدون", "web", "1332"), ("كم ارتفاع برج خليفة", "web", "828"), ("كم مساحة السعودية", "web", "كم²"),
    ("من مؤسس جوجل", "web", "لاري بايج"), ("who founded Tesla", "web", "Eberhard"), ("في اي قارة تقع البرازيل", "web", "أمريكا الجنوبية"),
    ("how tall is Mount Everest", "web", "8,849"), ("when was Steve Jobs born", "web", "1955"), ("من رئيس فرنسا", "web", "ماكرون"),
    ("ما هي اللغة الرسمية في سويسرا", "web", "الألمانية"), ("where was Albert Einstein born", "web", "Ulm"), ("area of Japan", "web", "km²"),
    ("قلي عن الخوارزمي", "web", "الخوارزمي"), ("عطني معلومات عن نهر النيل", "web", "النيل"), ("ايش هو الذكاء الاصطناعي", "web", "ذكاء"),
    ("اشرح الثقب الأسود باختصار", "web", "ثقب"), ("وش الجو في الدمام", "weather", "°"), ("الساعة كم", "datetime", "🕐"),
    ("ابغى احول 100 دولار لريال", "currency", "ريال سعودي"), ("هلا والله", "chat", "أهلاً"), ("شخبارك", "chat", ""),
    ("سوي لي كود حلقة for في بايثون", "code", "range"), ("عطني كود اقرا ملف بالجافاسكربت", "code", "readFileSync"),
    ("وش ناتج 45 زائد 55", "python", "100"),
    # --- system, public visitors get a safe refusal (2)
    ("run command `whoami`", "system", "developer's machine"), ("نفذ الامر `hostname`", "system", "جهاز المطوّر"),
]
