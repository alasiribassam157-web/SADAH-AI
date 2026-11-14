"""[18] Code synthesizer agent: builds a new Python program for a multi-step request
(«برنامج يقرأ ملف ثم يرتب الأسطر ثم يكتبها في ملف جديد») by combining verified blocks from code_kb.

Each step is recognised by the coder brain, its verified snippet is parsed into an AST, wrapped in its
own function, and a main() calls the steps in order.  The program is checked with ast.parse and
compile() — it is never executed.  Steps stay independent: SADAH says so instead of inventing glue code.
"""
import ast
import re
import textwrap

from agent.base_agent import AgentResult, BaseAgent, Task
from agent.code_kb import TASKS, snippet
from agent.coder import CONFIDENCE_FLOOR, CoderSkill

_SPLIT = re.compile(r"\s*(?:،|,|؛|;|\bثم\b|\bبعدين\b|\bوبعدها\b|\bبعدها\b|\bthen\b|\band then\b)\s*|\s+و(?=[يتأا]\S)",
                    re.IGNORECASE)
_LEAD = re.compile(r"^(?:اكتب|سو|سوي|ابي|أبي|ابغى|أبغى|اعطني|write|make|create|build)?\s*(?:لي\s+|me\s+)?(?:an?\s+)?"
                   r"(?:python\s+)?(?:برنامج|سكربت|كود|program|script|code)?\s*(?:بايثون|python)?\s*"
                   r"(?:يقوم ب|that|which|to)?\s*", re.I)
MAX_STEPS = 6
# «يطبع النتيجة» is not «Hello World»: every verified block already prints its own result
_SHOW_RESULT = re.compile(r"^(?:ي|ت)?(?:طبع|عرض|ظهر)\S*\s+(?:ال)?(?:نتيج|ناتج|مخرج|خرج)|"
                          r"^(?:print|show|display|output)s?\s+(?:the\s+)?(?:result|output|answer|count)", re.I)
_HELLO = re.compile(r"hello|مرحب|اهلا|أهلا", re.I)
# «يرتب قائمة» → «ترتيب قائمة»: the coder brain learned task names, so verbs are turned into nouns
MASDAR = {"قرأ": "قراءة", "كتب": "الكتابة", "رتب": "ترتيب", "عكس": "عكس", "حذف": "حذف", "حسب": "حساب", "طبع": "طباعة",
          "قسم": "تقسيم", "دمج": "دمج", "بحث": "بحث", "جمع": "جمع", "حول": "تحويل", "نشئ": "إنشاء", "قارن": "مقارنة",
          "عرف": "تعريف", "ولد": "توليد", "رسل": "إرسال", "حلل": "تحليل", "خزن": "تخزين", "فرز": "فرز"}


def phrasings(clause: str) -> list[str]:
    """The clause as written, as a task name («ترتيب قائمة بايثون») and as a how-to question."""
    words = clause.split()
    if words and re.fullmatch(r"[a-z]+s", words[0], re.I):   # «sorts a list» → «sort a list»
        return [clause, " ".join([words[0][:-1], *words[1:]])]
    stem = words[0][1:] if words and words[0][:1] in "يت" else ""
    out = [clause]
    if stem in MASDAR:
        out.append(" ".join([MASDAR[stem], *words[1:], "بايثون"]))
    if stem:
        out.append(" ".join(["كيف", "أ" + stem, *words[1:], "في بايثون"]))
    return out


def steps(text: str) -> list[str]:
    """The request's clauses, in order («يقرأ ملف ثم يرتب الأسطر» → two clauses)."""
    body = _LEAD.sub("", text.strip(" .؟?"), count=1)
    return [c.strip() for c in _SPLIT.split(body) if c and len(c.strip()) > 2][:MAX_STEPS]


def is_multi_step(text: str) -> bool:
    return bool(re.search(r"برنامج|سكربت|program|script", text, re.I)) and len(steps(text)) >= 2


def assemble(blocks: list[tuple[str, str]]) -> str:
    """One function per verified block plus main(); raises SyntaxError if any block is broken."""
    parts, calls = ['"""Program assembled by SADAH from verified building blocks."""', ""], []
    for i, (task, code) in enumerate(blocks, 1):
        ast.parse(code)                                    # each block must be valid on its own
        name = f"step_{i}_{task}"
        doc = TASKS[task][1]
        parts += [f"def {name}():", f'    """Step {i}: {doc}."""', textwrap.indent(code.strip(), "    "), "", ""]
        calls.append(f"    {name}()")
    parts += ["def main():", *calls, "", "", 'if __name__ == "__main__":', "    main()"]
    program = "\n".join(parts) + "\n"
    compile(program, "<sadah>", "exec")                     # compiled to bytecode only, never run
    return program


class CodeSynthesizerAgent(BaseAgent):
    name = "CodeSynthesizer"
    sector = "البرمجة والأمان"
    intents = frozenset({"code"})
    keywords = r"برنامج|سكربت|program|script"
    timeout = 4.0

    def __init__(self, coder: CoderSkill | None = None):
        super().__init__()
        self.coder = coder or CoderSkill()

    def can_handle(self, task: Task) -> float:
        return 0.9 if is_multi_step(task.text) else 0.0

    def handle(self, task: Task) -> AgentResult:
        clauses = steps(task.text)
        if len(clauses) < 2:
            return self.fail("الطلب خطوة واحدة؛ وكيل البرمجة الأساسي أنسب له")
        if not self.coder.brain.ready and not self.coder.brain.reload():
            return self.fail("عقل البرمجة غير جاهز")
        blocks, seen = [], set()
        for clause in clauses:
            if _SHOW_RESULT.search(clause) and not _HELLO.search(clause):
                self.step(f"«{clause}» ← كل خطوة تطبع ناتجها أصلًا", "لا حاجة لكتلة إضافية", confidence=0.9)
                continue
            kind, conf, _ = max((self.coder.brain.predict(p) for p in phrasings(clause)), key=lambda r: r[1])
            code = snippet(kind, "python") if conf >= CONFIDENCE_FLOOR else None
            self.step(f"«{clause}» ← {TASKS.get(kind, (kind,))[0]}", f"ثقة {conf:.0%}",
                      "ok" if code else "warn", conf)
            if code and kind not in seen:
                blocks.append((kind, code))
                seen.add(kind)
        if len(blocks) < 2:
            return self.fail("لم أتعرف على خطوتين برمجيتين على الأقل في الطلب")
        try:
            program = assemble(blocks)
        except SyntaxError as err:
            return self.fail(f"تعذّر تركيب البرنامج: {err.msg}")
        self.step("تحققتُ: البرنامج المركّب سليم الصياغة ويُترجَم (compile) دون تشغيله", confidence=0.85)
        titles = (" ← " if task.lang == "ar" else " → ").join(TASKS[k][0 if task.lang == "ar" else 1] for k, _ in blocks)
        note = ("ℹ️ كل خطوة كتلة موثّقة مستقلة؛ اربط المدخلات والمخرجات بين الخطوات حسب ملفاتك وبياناتك."
                if task.lang == "ar" else "ℹ️ Each step is an independent verified block; connect their inputs and "
                                          "outputs to your own files and data.")
        count = "خطوتين" if len(blocks) == 2 else f"{len(blocks)} خطوات"
        head = f"**برنامج من {count}:** {titles}" if task.lang == "ar" else \
            f"**A {len(blocks)}-step program:** {titles}"
        return self.ok(f"{head}\n\n```python\n{program}```\n\n{note}", 0.85,
                       data={"tasks": [k for k, _ in blocks]}, entity="python")
