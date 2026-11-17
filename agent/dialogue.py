"""Dialogue skills: catch the visitor's name, and keep everyday talk with the companion — never a search.

`encyclopedic()` / `is_chatty()` are used by the critic (a conversational message is never sent to Wiki,
the library, Translation or Synthesis); `capture()` and `chatty_reply()` are used by the companion.
"""
import random
import re

from agent import personal_gate
from agent.chat_replies import is_small_talk

_W = r"[؀-ۿa-zA-Z]"
# a clear encyclopedic opening: only these may leave the companion when the brain says «chat»
_ENCY = re.compile(r"^\s*(?:ما هو|ما هي|ماهو|ماهي|من هو|من هي|أين تقع|اين تقع|كم عدد|متى تأسس|متى تاسس|"
                   r"لماذا يحدث|كيف يعمل|what is|what are|who is|who was|where is|how does|why does)\b", re.I)
_COMMAND = re.compile(r"^\s*(?:ترجم|ترجمة|احسب|حول|ابحث|translate|convert|calculate|search)\b", re.I)
_CHATTY = re.compile(
    r"(?<!\w)(?:أنا|انا|إني|اني|اسمي|إسمي|فهمت|تفهم|تفهمني|اقصد|أقصد|اقصده|أقصده|اقول|أقول|لك|معي|يعمي|"
    r"يا عمي|يا اختي|يا سداة|يا سَداة|انت|أنت|انتي|أنتِ|شفيك|ركز|ركزي|غلط|خطأ|صح|نعم|لا|ايوه)(?!\w)", re.I)
_NAME = re.compile(
    rf"(?<!\w)(?:اسمي|إسمي|ناديني|نادني|(?:قول|قولي)\s+لي|(?:اقول|أقول)\s+لك\s+(?:انا|أنا)|"
    rf"(?:يا\s+)?عمي\s+(?:انا|أنا)|انا|أنا)\s+({_W}{{2,15}})\s*$")
_NOT_NAME = set("""هنا بخير تمام فاهم فاهمة طالب طالبة من في ب مع هذا هذه كذا جدا مره مرة بس شي وش ايش مين كيف ليش ليه
هل ما لا نعم ايوه كويس كويسة زين طيب جاهز جاهزة موجود موجودة معك عندك هناك متأكد متأكدة مهندس مهندسة مبرمج مبرمجة معلم
معلمة دكتور دكتورة طبيب طبيبة محاسب محاسبة موظف موظفة مصمم مصممة متقاعد محامي ممرض ممرضة زعلان زعلانه حزين حزينة تعبان
تعبانة مرهق مرهقة قلقان قلقانة متوتر متوترة خايف خايفة معصب معصبة مبسوط مبسوطة فرحان فرحانة سعيد سعيدة متحمس متحمسة
اللي الي هو هي انت أنت اعرف أعرف احب أحب ابغى ابي اريد أريد اقول أقول اقصد أقصد قلت قال""".split())
_NAMES = set("""بسام محمد أحمد احمد علي عمر خالد سعد فهد سلمان عبدالله يوسف ابراهيم إبراهيم حسن حسين ماجد سلطان فيصل نايف
تركي سارة نورة فاطمة مريم ليلى هند رنا منى سلمى""".split())
_VERB = re.compile(r"^[اأ](?:حب|بغ|بي|ريد|عرف|قدر|عمل|شتغل|سكن|درس|روح|قرا|كره|فضل|شوف|سمع)|\S+ك$")
_CLEAR = re.compile(r"فهمت|تفهم|اقصد|أقصد|ركز|شفيك|يعمي|عمي|غلط|خطأ|اختي", re.I)
_YES = re.compile(r"(?<!\w)(?:نعم|ايوه|صح)(?!\w)")
_BAD = re.compile(r"(?<!\w)لا(?!\w)")
REPLIES = {
    "clear": ["أعتذر منك لو التبس عليّ الأمر، وضّح لي قصدك أكثر وأنا معك. 🤍",
              "نعم أحاول أفهم قصدك، تفضل كمّل لي وأنا أسمعك. 🤍"],
    "yes": ["تمام 🤍 تفضل كمّل لي، أنا معك.", "حاضر! كمّل وأنا أسمعك. 😊"],
    "no": ["ولا يهمك، وضّح لي قصدك أكثر وأنا معك. 🤍", "خذ راحتك، قل لي وش تبي بالضبط. 🤍"],
    "any": ["أنا معك 🤍 تفضل كمّل، أو اسألني أي سؤال وأجاوبك.", "سمعتك 😊 كمّل كلامك أو اسألني أي شي تبي."],
    "name": ["أهلاً بك 🤍 إذا تقصد تعرّفني بنفسك قل «اسمي ...»، وإذا تبي أبحث عن شخص قل «من هو ...».",
             "حياك الله 🤍 تبي تعرّفني بنفسك؟ قل «اسمي ...»، أو اسأل «من هو ...» وأبحث لك."],
}


def encyclopedic(msg: str) -> bool:
    return bool(_ENCY.search(msg))


def _single_name(msg: str) -> bool:
    return msg.strip(" ؟?!.،") in _NAMES


def is_chatty(msg: str) -> bool:
    """Everyday talk (pronouns, «فهمت؟», «لا يعمي»…) or a bare common first name: never a search."""
    if _COMMAND.search(msg) or encyclopedic(msg):
        return False
    return bool(_CHATTY.search(msg)) or _single_name(msg)


def capture(st: dict, text: str, ar: bool) -> str | None:
    """Learn the name from «بسام» (when it was just asked), «أنا بسام», «لا يعمي انا بسام»…"""
    words = text.split()
    name = ""
    if _COMMAND.search(text) or _VERB.match(text.split()[-1] if words else ""):   # «ترجم انا احبك», «انا احب …»
        st["awaiting"] = False
        return None
    if st.get("awaiting") and len(words) == 1 and words[0] not in _NOT_NAME and re.fullmatch(rf"{_W}{{2,15}}", words[0]):
        name = words[0]
    elif (m := _NAME.search(text)) and m.group(1) not in _NOT_NAME and not m.group(1).startswith("ال"):
        name = m.group(1)
    st["awaiting"] = False
    if not name:
        return None
    again = st["name"] == name
    st["name"] = name
    if ar:
        return (f"أهلاً بك يا {name}، اسمك محفوظ عندي! 🤍" if again else
                f"تشرفت بك يا {name}! حفظت اسمك في ذاكرتي، كيف أقدر أساعدك اليوم؟ 🌟")
    return f"Nice to meet you, {name}! I saved your name. How can I help today?"


def chatty_reply(st: dict, text: str, ar: bool) -> str | None:
    """A natural conversational reply for a chatty message (so it never reaches a search)."""
    known = personal_gate.about_sadah(text) or (is_small_talk(text) and "سداة" not in text and "سَداة" not in text)
    if known or not is_chatty(text) or not ar:   # «من أنت» / «ساعدني» have their own answers
        return None
    kind = ("name" if _single_name(text) else "clear" if _CLEAR.search(text) else "yes" if _YES.search(text)
            else "no" if _BAD.search(text) else "any")
    options = [o for o in REPLIES[kind] if o != st["last"].get("dlg")] or REPLIES[kind]
    st["last"]["dlg"] = random.choice(options)
    return st["last"]["dlg"]
