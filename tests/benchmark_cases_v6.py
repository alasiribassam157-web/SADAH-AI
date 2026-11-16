"""SADAH v6 benchmark additions: markets, world currencies, conversation, knowledge library, new code tasks (30)."""

CASES_V6 = [
    # --- live markets (4)
    ("كم سعر الذهب اليوم", "currency", "عيار 21"), ("bitcoin price", "currency", "bitcoin"),
    ("سعر الفضة", "currency", "الجرام"), ("اسعار العملات الرقمية", "currency", "إيثيريوم"),
    # --- world currencies (6)
    ("الدينار الكويتي كم ريال", "currency", "دينار كويتي"), ("how many euros for 500 dollars", "currency", "500 US dollar"),
    ("حول لي 2000 ين", "currency", "ين ياباني"), ("كم 100 فرنك سويسري بالريال", "currency", "فرنك سويسري"),
    ("بكم الجنيه الاسترليني", "currency", "جنيه إسترليني"), ("كم الروبل بالريال", "currency", "روبل روسي"),
    # --- conversation (8)
    ("اسمي بسام", "chat", "بسام"), ("انا من جدة", "chat", "جدة"), ("انا طفشان", "chat", "الطفش"),
    ("انا متضايق", "chat", "أسمعك"), ("من وين انت", "chat", "السحابة"), ("نكتة", "chat", "😄"),
    ("I am tired", "chat", "rest"), ("وش تعرف عني", "chat", "عرّفني"),
    # --- knowledge library (5)
    ("ما هو التعلم الآلي", "web", "تعلم"), ("what is backpropagation", "web", "gradient"),
    ("ما هو التضخم", "web", "تضخم"), ("what is a transformer in deep learning", "web", "attention"),
    ("what is the chain rule", "web", "derivative"),
    # --- new code tasks (5)
    ("binary search in java", "code", "binarySearch"), ("كيف اسوي thread في بايثون", "code", "threading"),
    ("write a unit test in python", "code", "unittest"), ("quicksort java", "code", "quicksort"),
    ("الوراثة في جافا", "code", "extends"),
    # --- arithmetic and units phrasing (2)
    ("لو ضربت 23 في 19 كم يطلع", "python", "437"), ("كم مللي في لتر", "units", "1,000"),
]
