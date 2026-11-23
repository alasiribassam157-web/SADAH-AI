"""The conversation: (messages so far, current project) -> the assistant's next message, and the site when this turn built or changed one.

Stateless like the rest of sadah: the browser sends the whole conversation, the server replays the person's earlier messages to recover what is still
being asked («وش اسم المشروع؟» → the next short message is the name), then answers the last one. Rules only: no outside model, nothing leaves the server."""
import re
from dataclasses import dataclass, field

from builder import chattext as T, edit, specio
from builder.ml import design
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
    asked: str = ""     # what the last question was about: "name", or one of chattext.FIELDS
    skipped: tuple = ()  # interview questions the person waved away
    about: str = ""      # the request that made the project: what the design model reads


@dataclass
class Turn:
    reply: str
    suggestions: list[str] = field(default_factory=list)
    result: Result | None = None
    spec: Spec | None = None


def clean(messages) -> list[tuple[str, str]]:
    """The last MAX_MESSAGES messages as (role, text), anything malformed dropped."""
    out = []
    for m in messages if isinstance(messages, list) else []:
        if isinstance(m, dict) and m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str) and m["content"].strip():
            out.append((m["role"], " ".join(m["content"].split())[:MAX_CHARS]))
    return out[-MAX_MESSAGES:]


_SKIP = re.compile(r"^(?:لا|تخطى|خلاص|بعدين|ما ابي|مو لازم|ما له داعي|ماله داعي|كذا حلو|عادي)(?![ء-ي])")
_YES = re.compile(r"^(?:طبّ?قه|طبّ?ق|ايوه|ايه|ايوا|نعم|اي|تمام|اوكي|ok|يلا|ابشر|موافق|حلو|زين)(?![ء-ي])")
_NAMEHELP = re.compile(r"اقترح|اختر لي|انت اختر|ما ادري|مدري|ماعندي|ما عندي|اي اسم|فكره|ساعدني")
_PHONE = re.compile(r"(?<!\d)(\+?\d{9,13})(?!\d)")
_FIELD_EDIT = {"colour": "غير اللون الى {}", "theme": "خله {}"}


def _built(st: State, r: Result, text: str, new: bool, note: str = "") -> tuple[State, str, list[str], Result]:
    skipped, about = ((), text) if new else (st.skipped, st.about)
    field = T.next_field(r.spec, skipped, about)
    return State(r.spec, asked=field, skipped=skipped, about=about), T.built(r.spec, new, text, note, field, about), T.CHOICES.get(field, []), r


def _answer(st: State, text: str, nt: str) -> tuple[State, str, list[str], Result | None] | None:
    """The person's reply to an interview question: skip it, or apply it as an edit. None when it is not an answer (it is handled as a normal message)."""
    field = st.asked
    if _SKIP.match(nt):
        skipped = st.skipped + (field,)
        nxt = T.next_field(st.spec, skipped, st.about)
        return State(st.spec, asked=nxt, skipped=skipped, about=st.about), T.question(nxt, st.spec, st.about) if nxt else T.DONE, T.CHOICES.get(nxt, []), None
    if field == "design":
        s = design.suggest(st.spec, st.about)
        if s and _YES.match(nt):
            return _built(st, render(design.apply(st.spec, s)), text, False, "طبّقت التصميم المقترح.")
        return None
    instruction = ""
    if field == "phone" and (m := _PHONE.search(nt.replace(" ", ""))):
        instruction = f"اضف رقم جوالي {m.group(1)}"
    elif field in _FIELD_EDIT and len(nt.split()) <= 3:
        instruction = _FIELD_EDIT[field].format(text)
    done = edit.apply(st.spec, instruction) if instruction else None
    return _built(st, render(done.spec), text, False, done.note) if done and done.changed else None


def _step(st: State, text: str) -> tuple[State, str, list[str], Result | None]:
    nt = n(text).strip()
    if st.asked == "name" and st.pending and _NAMEHELP.search(nt):
        picks = design.names(st.pending, text)
        return st, T.name_ideas(picks), picks, None
    if st.asked == "name" and st.pending and len(nt.split()) <= 5 and not (_KIND.search(nt) or _REQUEST.search(nt)):
        marker = "" if re.match(r"(?:باسم|اسمه|اسمها|الاسم)\b", nt) else " باسم"
        text = f"{st.pending}{marker} {text}"
        nt = n(text)
    elif st.pending:
        text, nt = f"{st.pending} {text}", n(f"{st.pending} {text}")
    elif st.spec and st.asked in T.FIELDS and (got := _answer(st, text, nt)):
        return got
    elif _THANKS.search(nt):
        return st, T.pick(T.THANKS, text), [], None
    elif _CAN.search(nt):
        return st, T.CAN, T.START[:3], None
    elif st.spec and _SUMMARY.search(nt):
        return st, "هذا اللي عندي الحين: " + T.summary(st.spec), T.missing(st.spec), None
    elif _GREET.search(nt) and not _KIND.search(nt) and len(nt.split()) <= 6:
        return st, T.pick(T.HELLO, text), T.START, None
    elif st.spec and design.wants(nt):
        s = design.suggest(st.spec, st.about)
        if not s:
            return st, T.NO_DOMAIN, [], None
        return _built(st, render(design.apply(st.spec, s)), text, False, f"اخترت لك التصميم المناسب لمجال «{s.label}».")
    elif st.spec and (m := re.match(r"(?:باسم|اسمه|اسمها|الاسم)\s+(.+)", nt)):   # «باسم الملوك» after a build is a rename
        text = "غير الاسم الى " + " ".join(text.split()[1:])
        done = edit.apply(st.spec, text)
        if done.changed:
            return _built(st, render(done.spec), text, False, done.note)
    elif st.spec and _EDIT.search(nt) and (done := edit.apply(st.spec, text)).changed:
        return _built(st, render(done.spec), text, False, done.note)
    if st.spec and not (_KIND.search(nt) or st.pending or "باسم" in nt):   # something said about the current project that no rule understood
        if st.asked in T.FIELDS:
            return st, "ما فهمت جوابك. " + T.question(st.asked, st.spec, st.about), T.CHOICES[st.asked], None
        return st, "ما فهمت التعديل. جرّب مثلًا:", T.missing(st.spec), None
    if not (_KIND.search(nt) or st.pending or "باسم" in nt):
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


def turn(messages, spec_data=None) -> Turn:
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
    st, reply, sug, res = _step(st, users[-1])
    return Turn(reply, sug, res, res.spec if res else st.spec)

