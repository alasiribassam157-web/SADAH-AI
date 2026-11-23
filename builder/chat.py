"""The conversation: (messages so far, current project) -> the assistant's next message, and the site when this turn built or changed one.

Stateless like the rest of sadah: the browser sends the whole conversation, the server replays the person's earlier messages to recover what is still
being asked («وش اسم المشروع؟» → the next short message is the name), then answers the last one. Rules only. When the site owner turns on a model
(builder/llm.py) the same replay supplies the context and the model does the talking, while this module's pipeline still builds the site."""
import re
from dataclasses import dataclass, field

from builder import chattext as T, edit, llm, specio
from builder.build import Result, build, render
from builder.norm import n
from builder.spec import Spec

MAX_MESSAGES, MAX_CHARS = 12, 800
_KIND = re.compile(r"(?<![ء-ي])(?:[وفب]?(?:ال)?)(?:موقع|متجر|تطبيق|لعبه|مدونه|دعوه|لوحه|داشبورد|بورتفوليو|ملف|سيره|حفل|حفله|صفحه|فعاليه|مؤتمر|نموذج)")
_EDIT = re.compile(r"(?<![ء-ي])(?:غير|بدل|خل|خله|خلها|اضف|اضيف|حط|شيل|احذف|زود|ضيف|رجع|ارجع|حول|اجعل|صير|ابدل)")
_GREET = re.compile(r"^(?:يا\s+)?(?:سلام|السلام|هلا|مرحبا|اهلا|اهلين|صباح|مساء|حياك|حياكم|هلا والله)")
_THANKS = re.compile(r"(?<![ء-ي])(?:شكرا|مشكور|تسلم|يعطيك|جزاك|الله يعافيك|ممنون)")
_CAN = re.compile(r"وش\s+(?:تسوي|تقدر|تعرف|خدماتك|تبني|تسويه)|ايش\s+(?:تسوي|تقدر)|ماذا\s+تفعل|(?:من|مين|وش)\s+انت|ساعدني|مساعده|كيف\s+استخدم")
_SUMMARY = re.compile(r"المتطلبات|وش\s+فهمت|لخص|ملخص|وش\s+سويت|وش\s+فيه|ايش\s+فهمت")
_REQUEST = re.compile(r"(?<![ء-ي])(?:ابغى|ابي|ابغا|اريد|سوي|سوه|اعمل|اعملي|صمم|ممكن)")


@dataclass
class State:
    spec: Spec | None = None
    pending: str = ""   # the request that was not complete yet
    asked: str = ""     # "name" when the last question was the project's name


@dataclass
class Turn:
    reply: str
    suggestions: list[str] = field(default_factory=list)
    result: Result | None = None
    spec: Spec | None = None
    engine: str = "rules"


def clean(messages) -> list[tuple[str, str]]:
    """The last MAX_MESSAGES messages as (role, text), anything malformed dropped."""
    out = []
    for m in messages if isinstance(messages, list) else []:
        if isinstance(m, dict) and m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str) and m["content"].strip():
            out.append((m["role"], " ".join(m["content"].split())[:MAX_CHARS]))
    return out[-MAX_MESSAGES:]


def _built(st: State, r: Result, text: str, new: bool, note: str = "") -> tuple[State, str, list[str], Result]:
    return State(spec=r.spec), T.built(r.spec, new, text, note), T.missing(r.spec), r


def _step(st: State, text: str) -> tuple[State, str, list[str], Result | None]:
    nt = n(text).strip()
    if st.asked == "name" and st.pending and len(nt.split()) <= 5 and not (_KIND.search(nt) or _REQUEST.search(nt)):
        marker = "" if re.match(r"(?:باسم|اسمه|اسمها|الاسم)\b", nt) else " باسم"
        text = f"{st.pending}{marker} {text}"
        nt = n(text)
    elif st.pending:
        text, nt = f"{st.pending} {text}", n(f"{st.pending} {text}")
    elif _THANKS.search(nt):
        return st, T.pick(T.THANKS, text), [], None
    elif _CAN.search(nt):
        return st, T.CAN, T.START[:3], None
    elif st.spec and _SUMMARY.search(nt):
        return st, "هذا اللي عندي الحين: " + T.summary(st.spec), T.missing(st.spec), None
    elif _GREET.search(nt) and not _KIND.search(nt) and len(nt.split()) <= 6:
        return st, T.pick(T.HELLO, text), T.START, None
    elif st.spec and (m := re.match(r"(?:باسم|اسمه|اسمها|الاسم)\s+(.+)", nt)):   # «باسم الملوك» after a build is a rename
        text = "غير الاسم الى " + " ".join(text.split()[1:])
        done = edit.apply(st.spec, text)
        if done.changed:
            return _built(st, render(done.spec), text, False, done.note)
    elif st.spec and _EDIT.search(nt):
        done = edit.apply(st.spec, text)
        if done.changed:
            return _built(st, render(done.spec), text, False, done.note)
    if not (_KIND.search(nt) or st.pending or "باسم" in nt or st.spec):
        return State(), "ما عرفت وش تبي بالضبط. تبي موقع، تطبيق صغير، ولا لعبة؟ جرّب مثلًا:", T.START, None
    r = build(text)
    if r.ok:
        return _built(st, r, text, True)
    if r.question:
        wants_name = "اسم" in r.question
        return State(spec=st.spec, pending=text, asked="name" if wants_name else "other"), (T.ask_name("", text) if wants_name else r.question), [], None
    if r.message:
        return State(spec=st.spec), "هذا اللي أقدر عليه الحين: " + r.message, T.START, None
    if st.spec:
        return st, "ما فهمت التعديل. جرّب مثلًا:", T.missing(st.spec), None
    return State(), "ما قدرت أبني هذا الطلب (" + "، ".join(r.problems) + "). جرّب تعيد صياغته.", T.START, None


def turn(messages, spec_data=None, use_model: bool = True) -> Turn:
    """The assistant's reply to the last user message in `messages`."""
    msgs = clean(messages)
    if not msgs or msgs[-1][0] != "user":
        return Turn("اكتب لي رسالتك وأنا أرد عليك.", T.START)
    spec, bad = specio.check(spec_data) if spec_data else (None, [])
    users = [t for role, t in msgs if role == "user"]
    st = State()
    for text in users[:-1]:
        st = _step(st, text)[0]
    if spec and not bad:
        st.spec = spec
    if use_model and llm.enabled() and (said := llm.ask(msgs, T.summary(st.spec) if st.spec else "")):
        return _from_model(st, said)
    st, reply, sug, res = _step(st, users[-1])
    return Turn(reply, sug, res, res.spec if res else st.spec)


def _from_model(st: State, said: str) -> Turn:
    """The model talked; if it also wrote a request or an edit in the exact words the rules understand, the rules build it."""
    reply, request, instruction = llm.parse(said)
    res = None
    if request:
        r = build(request)
        res = r if r.ok else None
        if not r.ok and (r.question or r.message):
            reply = f"{reply}\n{r.question or r.message}".strip()
    elif instruction and st.spec:
        done = edit.apply(st.spec, instruction)
        res = render(done.spec) if done.changed else None
        if not done.changed:
            reply = f"{reply}\n{done.note}".strip()
    spec = res.spec if res else st.spec
    return Turn(reply or T.pick(T.HELLO, said), T.missing(spec) if spec else T.START, res, spec, "model")
