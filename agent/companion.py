"""Conversation skill: talk like a person, not only question → answer.

Per browser session it remembers the person (name, city, job, likes), their mood, and the last
five messages, then answers chat with empathy, their name, and a natural follow-up question.
"""
import random
import re
import time
from collections import OrderedDict, deque

from agent import dialogue, personal_gate
from agent.critic_rules import keyword_intent
from agent.talk_bank import MOODS, TALK

MAX_SESSIONS, TTL = 2000, 3 * 3600
_NAME = re.compile(r"^(?:انا\s+|أنا\s+)?(?:اسمي|إسمي)\s+([\w؀-ۿ]{2,20})(?:\s+[\w؀-ۿ]{2,20})?\s*$|"
                   r"^(?:my name is|call me|i'?m called)\s+([a-z]{2,20})", re.I)
_CITY = re.compile(r"^(?:(?:انا|أنا)\s+من|(?:انا\s+|أنا\s+)?(?:ساكن في|ساكن ب|اسكن في|أسكن في))\s+([؀-ۿ\w]{2,20})\s*$|"
                   r"^i(?:'m| am) from\s+([a-z ]{2,25})$|^i live in\s+([a-z ]{2,25})$", re.I)
_JOB = re.compile(r"^(?:انا|أنا)\s+(طالب|طالبة|مهندس|مهندسة|مبرمج|مبرمجة|معلم|معلمة|دكتور|دكتورة|طبيب|طبيبة|"
                  r"محاسب|محاسبة|موظف|موظفة|مصمم|مصممة|متقاعد|محامي|ممرض|ممرضة)(\s+[؀-ۿ]+)?\s*$|"
                  r"^i(?:'m| am) an? (student|engineer|developer|programmer|teacher|doctor|nurse|designer|accountant)\s*$", re.I)
_LIKE = re.compile(r"^(?:انا\s+|أنا\s+)?(?:(?:احب|أحب|اعشق|أعشق)\s+|مهتمة? ب\s*)(.{2,30}?)\s*$|"
                   r"^i (?:love|like|enjoy)\s+(.{2,30})$", re.I)


def _word(pattern: str) -> re.Pattern:
    """Whole-word match: «ارق» must not fire inside «طارق», nor «ملل» inside «مللي»."""
    return re.compile(rf"(?<!\w)(?:{pattern})(?!\w)", re.I)
_PERSONAL = re.compile(r"^(?:انا|أنا|حاس|حاسس|احس|أحس|i'?m|i am|i feel|feeling)\b", re.I)


class Companion:
    def __init__(self):
        self._s: OrderedDict[str, dict] = OrderedDict()

    def _state(self, session: str) -> dict:
        st = self._s.get(session)
        if not st or time.time() - st["t"] > TTL:
            st = {"name": "", "city": "", "job": "", "likes": [], "age": "", "birth_year": "", "awaiting_age": False,
                  "mood": "", "awaiting": False, "last": {}, "turns": deque(maxlen=5)}
        st["t"] = time.time()
        if not session:  # no session id: a throw-away memory, never shared between visitors
            return st
        self._s[session] = st
        self._s.move_to_end(session)
        while len(self._s) > MAX_SESSIONS:
            self._s.popitem(last=False)
        return st

    def note(self, session: str, message: str, answer: str) -> None:
        if session:
            self._state(session)["turns"].append((message, answer[:200]))

    def export(self, session: str) -> dict:
        """The small context the browser keeps (localStorage) so a cold serverless container still knows the visitor."""
        st = self._s.get(session) or {}
        return {"user_name": st.get("name", ""), "user_city": st.get("city", ""), "awaiting_name": bool(st.get("awaiting")),
                "last_code": st.get("code", ""), "user_job": st.get("job", ""), "user_likes": list(st.get("likes", [])),
                "user_age": st.get("age", ""), "birth_year": st.get("birth_year", ""), "awaiting_age": bool(st.get("awaiting_age"))}

    def load(self, session: str, ctx: dict) -> None:
        if not session or not isinstance(ctx, dict):
            return
        st = self._state(session)
        for key, field in (("user_name", "name"), ("user_city", "city"), ("user_job", "job"), ("user_age", "age"),
                           ("birth_year", "birth_year")):
            if isinstance(ctx.get(key), str) and ctx[key].strip():
                st[field] = ctx[key].strip()[:25]
        st["awaiting"], st["awaiting_age"] = bool(ctx.get("awaiting_name")), bool(ctx.get("awaiting_age"))
        if isinstance(ctx.get("user_likes"), list):
            st["likes"] = [str(x)[:30] for x in ctx["user_likes"][:10]]
        st["code"] = ctx["last_code"][:120] if isinstance(ctx.get("last_code"), str) else st.get("code", "")

    state = lambda self, session: self._state(session)   # noqa: E731  (the understanding stage reads/writes it)

    def name(self, session: str) -> str:
        return self._s.get(session, {}).get("name", "") if session else ""

    def _n(self, st: dict, lang: str) -> str:
        return (f" يا {st['name']}" if lang == "ar" else f", {st['name']}") if st["name"] else ""

    def _pick(self, st: dict, key: str, options: list[str]) -> str:
        choices = [o for o in options if o != st["last"].get(key)] or options
        st["last"][key] = random.choice(choices)
        return st["last"][key]

    def respond(self, session: str, message: str, lang: str, neural: str = "", conf: float = 0.0) -> str | None:
        """A person-to-person reply, or None when this is a real question for the tools."""
        st = self._state(session)
        text = re.sub(r"[.!؟?،,]+\s*$", "", message.strip())
        ar = lang == "ar"
        if reply := personal_gate.capture_age(st, text, ar):   # «عمري 21» / «مواليد 2005» — remembered, never a date query
            return reply
        if m := _NAME.match(text):
            st["name"] = next(g for g in m.groups() if g).strip().title()
            return f"تشرفنا يا {st['name']}! 🌟 أنا سَداة. كيف أقدر أساعدك اليوم؟" if ar else \
                f"Nice to meet you, {st['name']}! 🌟 How can I help today?"
        if m := _CITY.match(text):
            st["city"] = next(g for g in m.groups() if g).strip()
            return f"يا هلا بأهل {st['city']}! 🏙 الحين أقدر أعطيك طقسها ومواقيت صلاتها بسرعة. وش أخبار الجو عندكم؟" if ar \
                else f"Oh nice, {st['city']}! 🏙 Ask me its weather or prayer times anytime."
        if m := _JOB.match(text):
            st["job"] = next(g for g in m.groups() if g).strip()
            return f"ما شاء الله{self._n(st, lang)}! {st['job']} 👏 وش أكثر شي تحبه في مجالك؟" if ar else \
                f"That's great{self._n(st, lang)}! What do you enjoy most about being a {st['job']}?"
        if m := _LIKE.match(text):
            st["likes"].append(next(g for g in m.groups() if g).strip())
            return f"حلو! {st['likes'][-1]} اختيار رهيب 😄 وش اللي شدّك له؟" if ar else \
                f"Nice! {st['likes'][-1]} is a great choice 😄 What got you into it?"
        if reply := personal_gate.answer(st, text, ar):
            return reply
        if re.search(r"(?:وش|ما|ايش) اسمي|تعرف اسمي|what(?:'s| is) my name", text, re.I):
            return (f"اسمك {st['name']} 😊" if st["name"] else "ما قلت لي اسمك للحين! وش اسمك؟") if ar else \
                (f"You're {st['name']} 😊" if st["name"] else "You haven't told me yet! What's your name?")
        if re.search(r"(?:وش|ايش) تعرف عني|what do you know about me", text, re.I):
            return self._profile(st, ar)
        if re.search(r"(?:وش|ايش) (?:سألتك|قلت لك|كان سؤالي) (?:قبل|أول|اول)|what did i (?:ask|say) before", text, re.I):
            past = [m for m, _ in st["turns"]]
            return (f"آخر شي قلته: «{past[-1]}»" if past else "هذي أول رسالة بيننا 😊") if ar else \
                (f"You last said: «{past[-1]}»" if past else "This is our first message 😊")
        if _PERSONAL.match(text) or len(text.split()) <= 3:
            for mood, (pat, rep_ar, rep_en) in MOODS.items():
                if _word(pat).search(text):
                    st["mood"] = mood
                    return (rep_ar if ar else rep_en).format(n=self._n(st, lang))
        if reply := dialogue.capture(st, text, ar):
            return reply
        if keyword_intent(text) not in (None, "chat"):  # «الجو عامل ايه في القاهرة» is weather, not small talk
            return None
        for key, pat, rep_ar, rep_en in TALK:
            if _word(pat).search(text):
                return self._pick(st, key, rep_ar if ar else rep_en).format(n=self._n(st, lang))
        if neural in ("web", "code", "python") and conf >= 0.7:   # the brain says knowledge / code question: not small talk
            return None
        return dialogue.chatty_reply(st, text, ar)

    def _profile(self, st: dict, ar: bool) -> str:
        facts = [(st["name"], "اسمك", "your name is"), (st["city"], "من", "you're from"),
                 (st["job"], "تشتغل", "you work as"), ("، ".join(st["likes"]), "تحب", "you like"),
                 ((f"{st['age']} سنة (مواليد {st['birth_year']})" if ar else f"{st['age']} (born {st['birth_year']})")
                  if st["age"] and st["birth_year"] else st["age"], "عمرك", "you are")]
        known = [f"{a} {v}" if ar else f"{e} {v}" for v, a, e in facts if v]
        if not known:
            return "للحين ما أعرف عنك شي 😊 عرّفني بنفسك!" if ar else "I don't know much yet 😊 Tell me about yourself!"
        return ("اللي أعرفه: " + "، ".join(known) + " 🤍") if ar else ("What I know: " + ", ".join(known) + " 🤍")
