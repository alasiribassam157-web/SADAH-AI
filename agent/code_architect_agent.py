"""[17] Code architect agent: the coder brain (NumPy, 45 tasks) picks the programming task and the
verified snippet library (code_kb, six languages) supplies the code (coder.py).

Check: Python code must parse (ast.parse) — it is read, never executed.
"""
import ast
import re

from agent.base_agent import AgentResult, BaseAgent, Task
from agent.code_kb import TASKS, detect_language
from agent.coder import CONFIDENCE_FLOOR, CoderSkill

_PY_BLOCK = re.compile(r"```python\n(.*?)```", re.S)


def parses(answer: str) -> bool | None:
    """True if every Python block parses, None when the answer has no Python code."""
    blocks = _PY_BLOCK.findall(answer)
    if not blocks:
        return None
    try:
        for block in blocks:
            ast.parse(block)
    except SyntaxError:
        return False
    return True


class CodeArchitectAgent(BaseAgent):
    name = "CodeArchitect"
    sector = "البرمجة والأمان"
    intents = frozenset({"code"})
    keywords = r"كود|برمج|دالة|حلقة|كلاس|بايثون|جافا|code|function|loop|class|python|java|javascript"
    timeout = 4.0

    def __init__(self, coder: CoderSkill | None = None):
        super().__init__()
        self.coder = coder or CoderSkill()

    def classify(self, text: str) -> tuple[str, float]:
        """(task, confidence) from the coder brain, or ("", 0) if it is not loaded."""
        if not self.coder.brain.ready and not self.coder.brain.reload():
            return "", 0.0
        task, conf, _ = self.coder.brain.predict(text)
        return task, conf

    def handle(self, task: Task) -> AgentResult:
        lang = detect_language(task.text) or "python"
        res, kind, conf = self.coder.answer(task.text)
        title = TASKS.get(kind, ("", ""))[0 if task.lang == "ar" else 1]
        self.step(f"عقل البرمجة: {title or kind}", f"اللغة: {lang} · الحد الأدنى للثقة {CONFIDENCE_FLOOR:.0%}",
                  confidence=conf)
        if not res.ok:
            return self.fail(res.output, {"task": kind, "confidence": conf})
        ok = parses(res.output)
        if ok is False:
            self.step("الكود لم يجتز فحص الصياغة", status="warn", confidence=0.3)
            return self.fail("مقطع الكود فيه خطأ صياغة؛ لن أعرضه.")
        if ok:
            self.step("تحققتُ: الكود سليم الصياغة (ast.parse) دون تشغيله", confidence=max(conf, 0.9))
        return self.ok(res.output, max(conf, 0.9) if ok else conf, data={"task": kind, "lang": lang}, entity=lang)
