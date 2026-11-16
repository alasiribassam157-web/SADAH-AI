"""Training templates for the router brain: which skill should answer a message."""
from core import templates_extra
from core.templates_code import PHRASES

INTENTS = ["chat", "python", "file", "web", "system", "code", "weather", "currency", "datetime", "units",
           "prayer", "translate"]

SLOTS = {
    "expr": ["2 + 2", "15 * 7", "sqrt(144)", "2 ** 10", "100 / 3", "sum of 1 to 100",
             "factorial of 10", "average of 4, 8, 15", "fibonacci 20", "prime numbers under 50"],
    "fname": ["notes.txt", "report.md", "data.csv", "todo.txt", "script.py", "summary.json"],
    "folder": ["projects", "reports", "images", "backup", "docs", "data"],
    "topic": ["artificial intelligence", "quantum computing", "Egypt", "the moon", "climate change",
              "machine learning", "Albert Einstein", "world war 2", "bitcoin", "the internet",
              "photosynthesis", "the Roman Empire", "Japan", "the Eiffel Tower", "DNA", "gravity",
              "الذكاء الاصطناعي", "مصر", "الفضاء", "تاريخ الحاسوب", "الطاقة الشمسية", "برج خليفة",
              "الحرب العالمية الثانية", "الثقب الأسود", "فيتامين د", "القهوة", "لغة بايثون", "السعودية",
              "فرنسا", "ابن سينا", "الدولة العثمانية", "المريخ", "الأهرامات", "نيوتن", "الخلية",
              "Google", "Apple", "Tesla", "the Nile", "Mount Everest", "Elon Musk", "Leonardo da Vinci", "Saturn",
              "the Great Wall of China", "COVID-19", "Brazil", "India", "Germany", "Canada", "Steve Jobs", "chess",
              "جوجل", "تسلا", "نهر النيل", "جبل إيفرست", "القمر", "الشمس", "ابن خلدون", "صلاح الدين الأيوبي",
              "الخوارزمي", "سور الصين العظيم", "كرة القدم", "الشطرنج", "اليابان", "الهند", "ألمانيا", "البرازيل"],
    "n": ["7", "15", "25", "100", "3.5", "1200", "48", "9", "250", "60"],
    "cmd": ["dir", "ipconfig", "whoami", "systeminfo", "tasklist", "echo hello",
            "ping google.com", "hostname", "date /t", "ver"],
    "lang": ["python", "javascript", "java", "c++", "c#", "go", "بايثون", "جافاسكربت", "جافا", "سي شارب"],
    "task": [p for phrases in PHRASES.values() for p in phrases],  # every coding task the coder brain knows
    "city": ["Riyadh", "Jeddah", "Cairo", "Dubai", "London", "Tokyo", "Paris", "New York", "Istanbul", "Berlin",
             "Madrid", "Toronto", "Sydney", "Mumbai", "Doha", "الرياض", "جدة", "مكة", "القاهرة", "دبي", "الدمام",
             "أبها", "لندن", "الكويت", "المدينة", "الطائف", "تبوك", "الخبر", "عمّان", "بيروت", "الدوحة", "مسقط",
             "المنامة", "اسطنبول"],
    "cur": ["dollar", "euro", "pound", "yen", "USD", "EUR", "SAR", "AED",
            "دولار", "ريال", "يورو", "جنيه", "درهم", "دينار كويتي", "ليرة تركية", "جنيه استرليني"],
    "unit": ["km", "miles", "meters", "feet", "inches", "kg", "pounds", "grams", "liters", "gallons",
             "celsius", "fahrenheit", "كيلومتر", "ميل", "متر", "قدم", "كيلوجرام", "رطل", "جرام", "لتر",
             "مئوية", "فهرنهايت", "جيجابايت", "ميجابايت"],
}

TEMPLATES = {
    "chat": [
        "hello", "hi there", "hey sadah", "good morning", "how are you", "who are you",
        "what can you do", "thanks", "thank you so much", "help", "tell me about yourself",
        "مرحبا", "اهلا", "السلام عليكم", "كيف حالك", "من انت", "ماذا تستطيع ان تفعل",
        "شكرا", "شكرا جزيلا", "ساعدني", "صباح الخير", "عرفني بنفسك",
        "thank you", "thanks a lot", "bye", "good evening", "how's it going", "nice to meet you",
        "شكرا لك", "مشكور", "يعطيك العافية", "مع السلامة", "مساء الخير", "هلا", "كيفك", "وش تقدر تسوي",
        "هلا والله", "ياهلا", "شخبارك", "وش اخبارك", "تمام", "ممتاز", "انت ذكي", "تصبح على خير", "الله يعطيك العافية",
        "ok", "cool", "nice", "great job", "you're smart", "good night", "see you", "hey there", "what's up",
    ],
    "python": [
        "calculate {expr}", "compute {expr}", "what is {expr}", "solve {expr}",
        "run python code to find {expr}", "execute this python code", "run this code", "evaluate {expr}",
        "احسب {expr}", "كم يساوي {expr}", "حل {expr}", "شغل كود بايثون", "نفذ هذا الكود",
        "كم يساوي {n} ضرب {n}", "{n} زائد {n}", "كم {n} ناقص {n}", "{n} قسمة {n}", "الجذر التربيعي لـ {n}",
        "what is {n} times {n}", "{n} plus {n}", "what is {n}% of {n}", "square root of {n}", "{n} divided by {n}",
        "كم {n}% من {n}", "احسب مضروب {n}", "{n} * {n}", "{n} + {n} - {n}", "كم يطلع {n} ضرب {n}",
        "اقسم {n} على {n}", "how much is {n} times {n}", "({n} + {n}) * {n}", "وش ناتج {n} زائد {n}",
    ],
    "file": [
        "create a file named {fname}", "create file {fname} with content hello",
        "read the file {fname}", "open {fname}", "show content of {fname}",
        "delete file {fname}", "list files", "list all files in {folder}",
        "make a folder called {folder}", "create directory {folder}",
        "write hello world to {fname}", "save this text in {fname}", "organize my files",
        "انشئ ملف {fname}", "اقرا الملف {fname}", "اعرض محتوى {fname}", "احذف الملف {fname}",
        "اعرض الملفات", "انشئ مجلد {folder}", "اكتب مرحبا في الملف {fname}", "احفظ هذا النص في {fname}",
    ],
    "web": [
        "search for {topic}", "search the web for {topic}", "find information about {topic}",
        "who is {topic}", "tell me about {topic}", "look up {topic}", "what do you know about {topic}",
        "ابحث عن {topic}", "ابحث في الانترنت عن {topic}", "معلومات عن {topic}",
        "من هو {topic}", "ما هو {topic}", "اخبرني عن {topic}", "ما هي {topic}", "متى {topic}",
        "متى انتهت {topic}", "أين يقع {topic}", "كم عدد سكان {topic}", "عاصمة {topic}", "اشرح {topic}",
        "تكلم عن {topic}", "وش هو {topic}", "تاريخ {topic}", "من اخترع {topic}", "من اكتشف {topic}",
        "when did {topic} end", "where is {topic}", "how does {topic} work", "explain {topic}",
        "what is the capital of {topic}", "who invented {topic}", "population of {topic}", "history of {topic}",
        "what is the currency of {topic}", "عملة {topic}", "وكم عدد سكانها", "and what is its capital",
        "متى ولد {topic}", "اين ولد {topic}", "كم طول {topic}", "كم ارتفاع {topic}", "كم مساحة {topic}",
        "من مؤسس {topic}", "من اسس {topic}", "من رئيس {topic}", "في اي قارة تقع {topic}", "قلي عن {topic}",
        "عطني معلومات عن {topic}", "ايش هو {topic}", "ابغى اعرف عن {topic}", "{topic} باختصار",
        "اشرح {topic} بالتفصيل", "when was {topic} born", "where was {topic} born", "how tall is {topic}",
        "area of {topic}", "who founded {topic}", "who is the president of {topic}", "which continent is {topic} in",
        "what are {topic}", "define {topic}", "summary of {topic}", "facts about {topic}", "{topic} in short",
    ],
    "system": [
        "run command {cmd}", "execute {cmd}", "run {cmd} in terminal", "system command {cmd}",
        "show system info", "check my ip address", "list running processes", "what is my computer name",
        "نفذ الامر {cmd}", "شغل الامر {cmd}", "اعرض معلومات النظام", "اعرض العمليات الجارية", "نفذ امر نظام {cmd}",
    ],
    "code": [
        "how to {task} in {lang}", "how do i {task} in {lang}", "{lang} code to {task}", "show me how to {task} in {lang}",
        "write {lang} code to {task}", "example of {task} in {lang}", "{task} {lang}", "{lang} example {task}",
        "كيف {task} في {lang}", "كيف {task} بلغة {lang}", "مثال {lang} {task}", "اكتب كود {lang} عشان {task}",
        "ابغى كود {lang} {task}", "علمني كيف {task} في {lang}", "كود {task} {lang}",
        "ابي كود {task}", "سوي لي كود {task} ب{lang}", "write a {lang} function to {task}", "{task} using {lang}",
        "give me {lang} code for {task}", "syntax to {task} in {lang}", "طريقة {task} في {lang}",
    ],
    "weather": [
        "weather in {city}", "what is the weather in {city}", "temperature in {city}", "is it hot in {city}",
        "weather today", "will it rain in {city}", "{city} weather", "how hot is it in {city}",
        "الطقس في {city}", "كيف الجو في {city}", "درجة الحرارة في {city}", "طقس {city}", "حالة الجو اليوم",
        "هل الجو حار في {city}", "كم درجة الحرارة في {city}", "الجو في {city} اليوم",
        "وش الجو في {city}", "هل بتمطر في {city}", "forecast for {city}", "how's the weather in {city}",
        "الحرارة كم في {city}", "is it cold in {city}", "كيف الطقس اليوم", "ايش الطقس في {city}",
    ],
    "currency": [
        "convert {n} {cur} to {cur}", "how much is {n} {cur} in {cur}", "{cur} to {cur}", "{cur} exchange rate",
        "price of the {cur}", "{n} {cur} in {cur}",
        "كم سعر ال{cur}", "حول {n} {cur} الى {cur}", "كم {n} {cur} بال{cur}", "سعر صرف {cur}", "{n} {cur} كم {cur}",
        "سعر {cur} مقابل {cur}", "ابغى احول {n} {cur} ل{cur}", "how many {cur} is {n} {cur}",
        "rate of {cur} against {cur}", "سعر ال{cur} اليوم", "{n} {cur} to {cur}",
    ],
    "datetime": [
        "what time is it", "what is the date today", "what day is it", "today's date", "hijri date today",
        "current time", "what is the hijri date", "كم الساعة", "كم الساعه الحين", "ما هو تاريخ اليوم",
        "التاريخ اليوم", "وش اليوم", "التاريخ الهجري", "كم التاريخ هجري", "اليوم كم بالهجري", "الوقت الان",
        "what's today's date", "what day of the week is it", "وش التاريخ", "التاريخ بالهجري", "today in hijri",
        "كم الوقت", "الساعة كم", "what's the time",
    ],
    "units": [
        "convert {n} {unit} to {unit}", "how many {unit} in {n} {unit}", "{n} {unit} to {unit}", "{n} {unit} in {unit}",
        "حول {n} {unit} الى {unit}", "كم {unit} في {n} {unit}", "{n} {unit} كم {unit}", "{n} {unit} يساوي كم {unit}",
        "{n} {unit} كم يعادل {unit}", "what is {n} {unit} in {unit}", "{n} {unit} equals how many {unit}",
        "تحويل {n} {unit} الى {unit}",
    ],
}

# SADAH v4: prayer times, translation, sports and Levantine/Egyptian dialects (core/templates_extra.py)
SLOTS.update(templates_extra.SLOTS)
for _intent, _extra in templates_extra.TEMPLATES.items():
    TEMPLATES.setdefault(_intent, []).extend(_extra)
