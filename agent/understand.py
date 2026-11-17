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
_LEAD = re.compile(r"^(?:طيب|طيّب|اوكي|أوكي|اها|آها|قصدي|أقصد|اقصد|لو سمحت|من فضلك|بالنسبة|عفوا|عفواً|"
                   r"يعني(?=\s+(?:كيف|وش|ليش|لماذا|متى|اين|أين|ما)))\s+")
_KNOW = re.compile(r"^(?:هل تعرف|هل تعرفين|تعرفين|تعرف|وش تعرف عن|ايش تعرف عن|كلمني عن|حدثني عن|سمعت عن|"
                   r"وش رايك في|وش رأيك في)\s+")
_TITLE = re.compile(r"(?<!\w)(?:الممثلة|الممثل|اللاعبة|اللاعب|العالمة|العالم|المخرجة|المخرج|الشاعرة|الشاعر|"
                    r"الرئيس|الملك|الأمير|الامير|المغني|المغنية|الكاتب|الكاتبة|مدينة|دولة|جزيرة)\s+")
_LANG = "|".join(sorted(map(re.escape, LANG_WORDS), key=len, reverse=True))
_ONLY_LANG = re.compile(rf"^(?:و\s*)?(?:بلغة\s+|ب|في\s+|ل)?({_LANG})$")
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
    """«بجافا» / «فيها» after a coding question -> the same question in the new (or the same) language."""
    bare = re.sub(r"[؟?!.،\s]+$", "", text.strip())
    if m := _ONLY_LANG.match(bare):
        old = next((w for w in LANG_WORDS if re.search(rf"(?<!\w){w}(?!\w)", last)), None)
        return last.replace(old, m.group(1), 1) if old else f"{last} بلغة {m.group(1)}"
    return last if _PRONOUN.search(bare) and len(bare.split()) <= 5 else None


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
            return " ".join(words[:i] + [m.group(1), subject])
    return None


def rewrite(text: str, st: dict, subject: str = "") -> tuple[str, str]:
    """(clean text, a short note on what was understood — empty when nothing changed)."""
    new = fix_spelling(text)
    while (m := _LEAD.match(new)) and len(new) > m.end():
        new = new[m.end():]
    if (m := _KNOW.match(new)) and not personal_gate.is_personal(new) and not dialogue.is_chatty(new[m.end():]):
        entity = _TITLE.sub("", new[m.end():]).strip(" ؟?")
        new = f"من هو {entity}" if entity else new
    else:
        new = _TITLE.sub("", new)
    if st.get("code") and (carried := carry_code(new, st["code"])):
        new = carried
    elif subject and (carried := carry_topic(new, subject)):
        new = carried
    return new, (f"«{text}» ← «{new}»" if new != text else "")
"""Understanding stage: the question is cleaned before any agent sees it.

1. spelling: «باتون / بايثن» -> «بايثون», «الطباعه» -> «الطباعة» (close match against the programming vocabulary)
2. conversational lead-ins and titles are dropped («طيب», «قصدي», «تعرف الممثل X» -> «من هو X»)
3. code carry-over: after a coding question, «طيب بجافا ؟» / «قصدي كيف الطباعه فيها ؟» re-ask the same task
`rewrite()` returns (new text, what was understood); the last coding question lives in the visitor's state.
"""
import difflib
import re

from agent import dialogue, personal_gate

LANG_WORDS = ["جافاسكريبت", "جافا سكريبت", "بايثون", "جافا", "سي بلس بلس", "سي شارب", "سي++", "جو"]
_LANG_NAMES = ["بايثون", "جافا", "جافاسكريبت"]   # fuzzy matching is limited to these: «الكويت» must never become «الكود»
_HA = {"الطباعه": "الطباعة", "طباعه": "طباعة", "الكتابه": "الكتابة", "كتابه": "كتابة"}
_LEAD = re.compile(r"^(?:طيب|طيّب|قصدي|أقصد|اقصد|لو سمحت|يعني(?=\s+كيف))\s+")
_KNOW = re.compile(r"^(?:هل تعرف|تعرفين|تعرف|وش تعرف عن|كلمني عن|حدثني عن)\s+")
_TITLE = re.compile(r"(?<!\w)(?:الممثلة|الممثل|اللاعب|العالم|المخرج|الشاعر|الرئيس|الملك|مدينة|دولة)\s+")
_LANG = "|".join(sorted(map(re.escape, LANG_WORDS), key=len, reverse=True))
_ONLY_LANG = re.compile(rf"^(?:و\s*)?(?:بلغة\s+|ب|في\s+|ل)?({_LANG})$")
_PRONOUN = re.compile(r"(?:فيها|بها|فيه|به)$")


def _fix(core: str) -> str:
    if core in _HA:
        return _HA[core]
    if core in _LANG_NAMES or (core[:1] in "بول" and core[1:] in _LANG_NAMES):
        return core
    for prefix in ("ب", "و", "ل", ""):   # «بباتون» keeps its «ب»
        if not core.startswith(prefix) or len(bare := core[len(prefix):]) < 5 or bare in _LANG_NAMES:
            continue
        if hit := difflib.get_close_matches(bare, _LANG_NAMES, 1, 0.72):
            return prefix + hit[0]
    return core


def fix_spelling(text: str) -> str:
    words = []
    for word in text.split():
        core = word.rstrip("؟?!.،")
        words.append(_fix(core) + word[len(core):])
    return " ".join(words)


def carry_code(text: str, last: str) -> str | None:
    """«بجافا» / «فيها» after a coding question -> the same question in the new (or the same) language."""
    bare = re.sub(r"[؟?!.،\s]+$", "", text.strip())
    if m := _ONLY_LANG.match(bare):
        old = next((w for w in LANG_WORDS if re.search(rf"(?<!\w){w}(?!\w)", last)), None)
        return last.replace(old, m.group(1), 1) if old else f"{last} بلغة {m.group(1)}"
    if _PRONOUN.search(bare) and re.search(r"كيف|طباع|الطباع|كتاب", bare):
        return last
    return None


def rewrite(text: str, st: dict) -> tuple[str, str]:
    """(clean text, a short note on what was understood — empty when nothing changed)."""
    new = fix_spelling(text)
    entity = ""
    while (m := _LEAD.match(new)) and len(new) > m.end():
        new = new[m.end():]
    if (m := _KNOW.match(new)) and not personal_gate.is_personal(new) and not dialogue.is_chatty(new[m.end():]):
        entity = _TITLE.sub("", new[m.end():]).strip(" ؟?")
        new = f"من هو {entity}" if entity else new
    else:
        new = _TITLE.sub("", new)
    if st.get("code") and (carried := carry_code(new, st["code"])):
        new = carried
    return new, (f"«{text}» ← «{new}»" if new != text else "")
