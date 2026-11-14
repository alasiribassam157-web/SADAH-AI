"""[01] Companion agent: talks with the person, keeps memory and mood, and writes the final reply.

Uses the existing conversation skills (companion.py, talk_bank.py, chat_replies.py, memory.py) and
speaks as SADAH, in the feminine: «سَداة تفكّر…», «تحققتُ من النتيجة…».
"""
import re

from agent.base_agent import AgentResult, BaseAgent, Task
from agent.chat_replies import chat_reply, is_small_talk
from agent.companion import Companion
from agent.memory import ConversationMemory

# Old identity in the reply banks -> the current one (the stored browser keys stay nexus_*).
_IDENTITY = [(re.compile(r"\*\*NEXUS(?:-1)?\*\*"), "**سَداة**"), (re.compile(r"منصة NEXUS|مشروع NEXUS"), "مشروع سَداة"),
             (re.compile(r"NEXUS team"), "SADAH team"), (re.compile(r"NEXUS(?:-1)?"), "سَداة")]
_EN_IDENTITY = [(re.compile(r"\*\*سَداة\*\*"), "**SADAH**"), (re.compile(r"سَداة"), "SADAH")]
# Masculine self-references in the old banks -> feminine (SADAH is «she»).
_FEMININE = [(re.compile(r"(?<!\w)أنا مساعد(?!\w)"), "أنا مساعدة"), (re.compile(r"(?<!\w)مساعد ذكي(?!\w)"), "مساعدة ذكية"),
             (re.compile(r"(?<!\w)عقل صغير دربناه(?!\w)"), "عقل صغير درّبناه")]
NO_ANSWER = {"ar": "بحثتُ في المصادر المتاحة ولم أجد إجابة موثوقة لهذا السؤال، فأفضّل ألا أخمّن. 🤍",
             "en": "I searched the sources I have and found no reliable answer, so I'd rather not guess. 🤍"}


def speak_as_sadah(text: str, lang: str) -> str:
    """Rename the old identity and use feminine self-references."""
    for pattern, new in _IDENTITY:
        text = pattern.sub(new, text)
    if lang == "en":
        for pattern, new in _EN_IDENTITY:
            text = pattern.sub(new, text)
        return text
    for pattern, new in _FEMININE:
        text = pattern.sub(new, text)
    return text


class CompanionAgent(BaseAgent):
    name = "Companion"
    sector = "القيادة والتواصل"
    intents = frozenset({"chat"})
    keywords = r"^(?:مرحبا|هلا|السلام|اهلا|أهلا|شكرا|hello|hi|hey|thanks)|اسمي|my name is|كيف حالك|how are you"
    timeout = 2.0

    def __init__(self):
        super().__init__()
        self.talk = Companion()
        self.memory = ConversationMemory()

    # --- memory, used by the orchestrator around every question
    def resolve(self, task: Task) -> Task:
        """«وكم عدد سكانها؟» -> «وكم عدد سكان اليابان» using the last subject of this conversation."""
        resolved = self.memory.resolve(task.session, task.text)
        if resolved != task.text:
            task.context["followup"] = f"{task.text} → {resolved}"
            task.text = resolved
        return task

    def remember(self, task: Task, result: AgentResult) -> None:
        self.memory.remember(task.session, result.entity)
        self.talk.note(task.session, task.text, result.answer)

    def person(self, session: str) -> str:
        return self.talk.name(session)

    # --- the agent itself: a person-to-person reply, or a polite «not mine»
    def handle(self, task: Task) -> AgentResult:
        self.step("سَداة تقرأ الرسالة", "هل هي دردشة أم سؤال يحتاج أداة؟")
        reply = self.talk.respond(task.session, task.text, task.lang)
        if reply:
            self.step("سَداة تردّ بشكل شخصي", "تتذكر الاسم والمزاج وآخر خمس رسائل")
            return self.ok(speak_as_sadah(reply, task.lang), 0.95)
        if is_small_talk(task.text):
            return self.ok(speak_as_sadah(chat_reply(task.text, task.lang), task.lang), 0.9)
        return self.fail("ليست دردشة، تحتاج وكيلًا متخصصًا")

    # --- the final reply that the person reads
    def compose(self, task: Task, results: list[AgentResult], badge: str = "", sources=()) -> str:
        """Join the successful answers (one per sub-question), then the critic's verdict and all sources
        (`sources` adds the witnesses' links when the critic confirmed the answer with them)."""
        good = [r for r in results if r.ok and r.answer.strip()]
        if not good:
            return NO_ANSWER[task.lang]
        parts = [speak_as_sadah(r.answer.strip(), task.lang) for r in good]
        body = "\n\n".join(parts)
        if badge:
            body += f"\n\n{badge}"
        links = [s for r in good for s in r.sources] + list(sources)
        links = [s for s in links if s.startswith("http") and s not in body]
        unique = list(dict.fromkeys(links))[:4]
        if unique:
            body += "\n\n" + "\n".join(f"🔗 {s}" for s in unique)
        name = self.person(task.session)
        if name and task.lang == "ar" and len(good) > 1:
            body = f"تفضّل يا {name}، هذا ما وجدته:\n\n" + body
        return body
