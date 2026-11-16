"""Short conversation memory: resolve follow-ups like «وكم عدد سكانها؟» to the last subject."""
import re
import time
from collections import OrderedDict

MAX_SESSIONS = 2000
TTL_SECONDS = 2 * 3600

# (pattern for a follow-up without its subject, rewrite using {e} = remembered subject)
_FOLLOW_UPS = [
    (r"عاصمت(?:ها|ه)", "عاصمة {e}"), (r"سكان(?:ها|ه)", "سكان {e}"), (r"عملت(?:ها|ه)", "عملة {e}"),
    (r"لغت(?:ها|ه) الرسمية|لغت(?:ها|ه)", "اللغة الرسمية في {e}"), (r"(?:تأسست|تاسست|تأسس|تاسس)\s*$", "تأسست {e}"),
    (r"(?:الجو|الطقس|الحرارة) (?:فيها|فيه|هناك)", "الطقس في {e}"),
    (r"\bits capital\b", "capital of {e}"), (r"\bits population\b|how many people live there", "population of {e}"),
    (r"\bits currency\b", "currency of {e}"), (r"\bwhen was it founded\b", "when was {e} founded"),
    (r"\bweather there\b", "weather in {e}"),
    (r"\bwhen was (?:he|she|it) born\b", "when was {e} born"), (r"\bwhere was (?:he|she) born\b", "where was {e} born"),
    (r"^و?\s*متى (?:ولد|ولدت|انولد)\s*$", "متى ولد {e}"), (r"^و?\s*(?:اين|أين|وين) (?:ولد|ولدت)\s*$", "أين ولد {e}"),
    (r"^(?:و\s*)?(?:المزيد|اكثر|أكثر|تكلم اكثر|زدني)\s*$", "معلومات عن {e}"),
    (r"^(?:tell me )?more\s*$", "tell me about {e}"),
    (r"^(?:و\s*)?(?:اشرح|وضح|وضّح|فصل|فصّل|كمل|كمّل)(?: لي)?(?: (?:اكثر|أكثر|بالتفصيل|زيادة))?\s*$", "{e} بالتفصيل"),
    (r"^(?:can you )?(?:explain|go on|continue)(?: more| in more detail| further)?\s*$", "{e} in detail"),
]

# A question that points back with «ـها / ـه» or «its / his / her» at something never named:
# «وكم عدد سكانها؟» «ما هي عاصمتها؟» «كم مساحته؟» «what is its capital»
_PROPS = (r"عاصمت|سكان|عملت|لغت|مساحت|ارتفاع|عمر|طول|وزن|موقع|رئيس|مؤسس|حجم|عدد|تاريخ|مدين|مناخ|اقتصاد|علم|تأسيس|ميلاد")
_DANGLING_AR = re.compile(rf"^(?:و\s*)?(?:(?:ما|كم|متى|اين|أين|وين|من)\s+)?(?:(?:هي|هو|هم)\s+)?(?:\S+\s+)?"
                          rf"((?:{_PROPS})\S*?)(?:ها|ه|هم)(?:\s+الرسمية)?$")
_DANGLING_EN = re.compile(r"\b(?:its|his|her|their)\s+(?:capital|population|currency|area|size|height|age|language|founder|"
                          r"president|weather|location)\b|\blive there\b|\bweather there\b", re.I)


def is_dangling(message: str) -> bool:
    """True for a short question that depends on a subject mentioned before (the caller checks the memory)."""
    text = re.sub(r"[؟?!.،,]+\s*$", "", message.strip())
    return len(text.split()) <= 6 and bool(_DANGLING_AR.search(text) or _DANGLING_EN.search(text))


class ConversationMemory:
    def __init__(self):
        self._sessions: OrderedDict[str, tuple[float, str]] = OrderedDict()

    def subject(self, session: str) -> str:
        stamp, entity = self._sessions.get(session, (0.0, ""))
        return entity if time.time() - stamp < TTL_SECONDS else ""

    def remember(self, session: str, entity: str) -> None:
        if not session or not entity:
            return
        self._sessions[session] = (time.time(), entity)
        self._sessions.move_to_end(session)
        while len(self._sessions) > MAX_SESSIONS:
            self._sessions.popitem(last=False)

    def resolve(self, session: str, message: str) -> str:
        """Rewrite a follow-up question to include the remembered subject (or return it unchanged)."""
        entity = self.subject(session)
        if not entity:
            return message
        text = re.sub(r"[؟?]+\s*$", "", message.strip())
        for pattern, rewrite in _FOLLOW_UPS:
            if re.search(pattern, text, re.IGNORECASE):
                return re.sub(pattern, rewrite.format(e=entity), text, count=1, flags=re.IGNORECASE)
        m = _DANGLING_AR.search(text)   # «كم مساحته» -> «كم مساحة اليابان»
        if m:
            word = m.group(0).split()[-1]
            stem = re.sub(r"(?:ها|ه|هم)$", "", word)
            return text[:len(text) - len(word)] + (stem[:-1] + "ة" if stem.endswith("ت") else stem) + f" {entity}"
        return message

    def dangling(self, session: str, message: str) -> bool:
        """A pointing-back question while this conversation has no subject yet: it must not become a search."""
        return not self.subject(session) and is_dangling(message)
