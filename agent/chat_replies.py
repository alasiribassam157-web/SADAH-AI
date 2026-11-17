"""Short conversational replies for greetings, thanks and questions about SADAH herself."""
import re

ABOUT = {
    "ar": "أنا **سَداة**، مساعدة ذكية بعقل مُدرَّب ذاتياً. اسألني عن أي معلومة، أو اطلب مني حساباً "
          "(مثل `احسب 15 ضرب 7`)، أو أنشئ لك ملاحظة (مثل `انشئ ملف ideas.txt`).",
    "en": "I'm **SADAH**, an assistant with a self-trained brain. Ask me about any topic, give me a "
          "calculation (like `15 times 7`), or have me save a note (like `create file ideas.txt`).",
}

# (keywords, Arabic reply, English reply); first match wins
RULES = [
    (("شكرا", "شكراً", "مشكور", "يعطيك العافية", "يسلمو", "تسلم", "متشكر", "thank", "thanks", "thx"),
     "العفو! 😊 إذا عندك سؤال ثاني أنا حاضر.", "You're welcome! 😊 Ask me anything else."),
    (("كيف حالك", "كيفك", "شلونك", "شخبارك", "وش اخبارك", "ازيك", "عامل ايه", "شو الاخبار", "how are you", "how's it going", "what's up"),
     "بخير الحمد لله، شكراً لسؤالك! كيف أقدر أساعدك؟", "I'm doing great, thanks! How can I help?"),
    (("تصبح على خير", "good night"), "وأنت من أهله! 🌙", "Good night! 🌙"),
    (("تمام", "ممتاز", "اوكي", "ok", "okay", "cool", "nice", "great job", "انت ذكي", "you're smart"),
     "يسعدني! 😊 وش نسوي الحين؟", "Glad to hear it! 😊 What's next?"),
    (("من انت", "من أنت", "من انتي", "من أنتي", "من أنتِ", "مين انت", "مين انتي", "مين أنتِ", "عرفيني بنفسك", "وش انت", "عرفني بنفسك", "ماذا تستطيع", "وش تقدر", "ساعدني",
      "who are you", "what can you do", "help", "about yourself"), None, None),
    (("صباح", "good morning"), "صباح النور! ☀️ كيف أقدر أساعدك؟", "Good morning! ☀️ How can I help?"),
    (("مساء", "good evening"), "مساء النور! 🌙 كيف أقدر أساعدك؟", "Good evening! 🌙 How can I help?"),
    (("مع السلامة", "باي", "bye", "goodbye", "see you"), "مع السلامة! 👋", "Goodbye! 👋"),
    (("السلام عليكم",), "وعليكم السلام ورحمة الله! كيف أقدر أساعدك؟", None),
]


GREETINGS = ("مرحبا", "اهلا", "أهلا", "هلا", "هلا والله", "ياهلا", "اهلين", "مرحبتين", "صباحو", "هاي", "hello", "hi", "hey", "hey there", "sadah", "سداة", "سَداة")


def _has(text: str, word: str) -> bool:
    # Whole-word match: "صباح" must not fire inside "المصباح".
    return re.search(rf"(?<!\w){re.escape(word)}(?!\w)", text) is not None


def is_small_talk(message: str) -> bool:
    low = message.lower()
    words = (w for keywords, _, _ in RULES for w in keywords)
    return any(_has(low, w) for w in (*words, *GREETINGS))


def chat_reply(message: str, lang: str) -> str:
    low = message.lower()
    for keywords, reply_ar, reply_en in RULES:
        if any(_has(low, k) for k in keywords):
            reply = reply_ar if lang == "ar" else reply_en
            return reply or ABOUT[lang]
    return "أهلاً! 👋 كيف أقدر أساعدك اليوم؟" if lang == "ar" else "Hi there! 👋 How can I help you today?"
