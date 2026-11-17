"""Understanding stage: every question is cleaned before any agent sees it.

1. spelling — any unknown word is corrected against the whole vocabulary (agent/lexicon.py), so new
   typos are handled too, not a list of known ones
2. conversational lead-ins and titles are dropped («طيب»، «قصدي»، «تعرف الممثل X» -> «من هو X»)
3. carry-over — «طيب بجافا ؟», «وكم عدد سكانها», «وش فوائده» re-ask the previous question about the new
   language, or about the subject the conversation is already on
`rewrite()` returns (new text, what was understood); the session's frame lives in the visitor's state.
"""
import re

from agent import arabic, dialogue, lexicon, personal_gate
from agent.code_kb import detect_language
LANG_WORDS = ["جافاسكريبت", "جافا سكريبت", "جافاسكربت", "بايثون", "جافا", "سي بلس بلس", "سي شارب", "سي++", "جو"]
_LEAD = re.compile(r"^(?:طيب لو|طيب|طيّب|اوكي|أوكي|اها|آها|قصدي|أقصد|اقصد|لو سمحت|من فضلك|بالنسبة|عفوا|عفواً|"
                   r"اقولك|أقولك|اقول لك|أقول لك|يا سداة|يا سَداة|اسمعيني|اسمعني|شوفي|شوف|ترى|ترا|والله|"
                   r"يعني(?=\s+(?:كيف|وش|ليش|لماذا|متى|اين|أين|ما)))\s+")
_ASKS = re.compile(r"^(?:كم|كيف|متى|أين|اين|وين|لماذا|ليش|ليه|وش|ايش|ما|ماذا|هل|احسب|ترجم|حول)(?!\w)")
_OWN = re.compile(r"عمري|اسمي|مدينتي|مواليد")   # «تعرف كم عمري» asks about the visitor, not about a famous name
_KEY_WORD = {"python": "بايثون", "javascript": "جافاسكريبت", "java": "جافا", "cpp": "C++", "csharp": "C#", "go": "جو"}
_FILLER = {"طيب", "كيف", "وش", "في", "ب", "بـ", "بلغة", "لغة", "كود", "الكود", "اكتبها", "اكتبه", "اكتب", "كمان", "ايضا", "بس"}
_KNOW = re.compile(r"^(?:هل تعرف|هل تعرفين|تعرفين|تعرف|وش تعرف عن|ايش تعرف عن|كلمني عن|حدثني عن|سمعت عن|"
                   r"وش رايك في|وش رأيك في)\s+")
_TITLE = re.compile(r"(?<!\w)(?:الممثلة|الممثل|اللاعبة|اللاعب|العالمة|العالم|المخرجة|المخرج|الشاعرة|الشاعر|"
                    r"الرئيس|الملك|الأمير|الامير|المغني|المغنية|الكاتب|الكاتبة|مدينة|دولة|جزيرة)\s+")
_PRONOUN = re.compile(r"(?:فيها|بها|فيه|به|عنها|عنه|عنهم|لها|له|منها|منه)(?!\w)")
_ATTACHED = re.compile(r"^(\S{3,})(?:ها|هم|ه)$")   # «فوائده», «سعرها»: a noun carrying a pronoun
_SHORT_FOLLOW = re.compile(r"^(?:و\s*)?(?:وش|ايش|كيف|ليش|لماذا|متى|اين|أين|كم|ما|هل)\b")


_LANG_SLOT = re.compile(r"((?<!\w)(?:بلغة|بلغه|لغة|لغه|باستخدام)\s+)(\S+)")


def fix_language(text: str) -> str:
    """Grammar, not a word list: whatever follows «بلغة» has to be the name of a language."""
    def swap(m: re.Match) -> str:
        word = m.group(2).strip("؟?!.،")
        if not word or detect_language(word):
            return m.group(0)
        hit = arabic.closest(word, LANG_WORDS, floor=0.55, margin=0.0)
        return m.group(1) + m.group(2).replace(word, hit, 1) if hit else m.group(0)
    return _LANG_SLOT.sub(swap, text)


def fix_spelling(text: str) -> str:
    """Correct any misspelled word against the system's whole vocabulary (the brains' 8000 BPE pieces,
    the 45 programming tasks and the 30 000 words of the offline library)."""
    return fix_language(lexicon.correct(text))


def carry_code(text: str, last: str) -> str | None:
    """«طيب بجافا» / «وكيف في جافا» / «اكتبها بـ C++» / «كيف الطباعة فيها» -> the last coding question,
    asked in the new language (or the same one)."""
    bare = re.sub(r"[؟?!.،\s]+$", "", text.strip())
    words = bare.split()
    new = detect_language(bare)
    leftover = [w for w in words if not detect_language(w) and (w.lstrip("و") or w) not in _FILLER]
    if new and len(words) <= 6 and not leftover:   # the language is all that changed
        old = next((w for w in last.split() if detect_language(w)), None)
        return last.replace(old, _KEY_WORD[new], 1) if old else f"{last} بلغة {_KEY_WORD[new]}"
    return last if _PRONOUN.search(bare) and len(words) <= 5 else None


def carry_topic(text: str, subject: str) -> str | None:
    """Any short question that points back inherits the subject, whichever agent answers it:
    «وش فوائده الثانية» -> «وش فوائد العسل», «كم سعره» -> «كم سعر الذهب»."""
    bare = re.sub(r"[؟?!.،\s]+$", "", text.strip())
    words = bare.split()
    if not subject or len(words) > 6 or not _SHORT_FOLLOW.match(bare):
        return None
    for i, word in enumerate(words):
        if _PRONOUN.fullmatch(word):
            return " ".join(words[:i] + [subject])
        if (m := _ATTACHED.match(word)) and not dialogue.is_chatty(word):
            return " ".join(words[:i] + [m.group(1), subject] + words[i + 1:])
    return None


def rewrite(text: str, st: dict, subject: str = "") -> tuple[str, str]:
    """(clean text, a short note on what was understood — empty when nothing changed)."""
    new = fix_spelling(text)
    while (m := _LEAD.match(new)) and len(new) > m.end():
        new = new[m.end():]
    if m := _KNOW.match(new):
        rest = new[m.end():]
        if personal_gate.is_personal(new):
            new = _TITLE.sub("", new)
        elif _ASKS.match(rest) or _OWN.search(rest):   # «تعرف كيف اطبع» stays a question, not «من هو كيف اطبع»
            new = rest.strip() or new
        elif not dialogue.is_chatty(rest):
            entity = _TITLE.sub("", rest).strip(" ؟?")
            new = f"من هو {entity}" if entity else new   # only a bare proper name becomes «من هو»
        else:
            new = _TITLE.sub("", new)
    else:
        new = _TITLE.sub("", new)
    if st.get("code") and (carried := carry_code(new, st["code"])):
        new = carried
    elif subject and (carried := carry_topic(new, subject)):
        new = carried
    return new, (f"«{text}» ← «{new}»" if new != text else "")
