"""[20] Critic & security agent: reviews the intent, checks code with AST, cross-checks sources,
and sends a question to an alternative agent when the first one fails.

Nothing here runs user code: code is only parsed (ast.parse) and inspected.
"""
import ast
import re

from agent import critic
from agent.base_agent import AgentResult, BaseAgent, Task
from agent.tools import _BLOCKED
from agents import consensus

BANNED_IMPORTS = {"os", "sys", "subprocess", "shutil", "socket", "ctypes", "pickle", "marshal", "importlib",
                  "multiprocessing", "threading", "signal", "pty", "requests", "httpx", "urllib", "builtins"}
BANNED_CALLS = {"eval", "exec", "compile", "__import__", "open", "input", "globals", "locals", "vars",
                "getattr", "setattr", "delattr", "breakpoint", "exit", "quit"}
FALLBACKS = {"Wikidata": ["Wiki", "LocalKB"], "Wiki": ["LocalKB", "Wikidata"], "LocalKB": ["Wiki", "Wikidata"],
             "OpenWeb": ["Wiki", "LocalKB"], "Synthesis": ["Wiki", "LocalKB"], "SymbolicMath": ["NumericMath"],
             "NumericMath": ["SymbolicMath"], "Forex": ["Markets"], "Markets": ["Forex"], "Units": ["NumericMath"],
             "CodeArchitect": ["CodeSynthesizer"], "CodeSynthesizer": ["CodeArchitect"], "Translation": ["Wiki"]}
KNOWLEDGE = {"Wikidata", "Wiki", "LocalKB", "OpenWeb", "Synthesis"}
BADGE = {"ar": {consensus.VERIFIED: "✅ **تحققتُ:** مصدران مستقلان متفقان.",
                consensus.SINGLE: "ℹ️ **مصدر واحد:** لم أجد مصدرًا ثانيًا يؤكد المعلومة أو ينفيها.",
                consensus.CONFLICT: "⚠️ **المصادر مختلفة:** المصدر الأول يذكر «{v}» والثاني «{s}». تحقّق قبل الاعتماد عليها."},
         "en": {consensus.VERIFIED: "✅ **Verified:** two independent sources agree.",
                consensus.SINGLE: "ℹ️ **Single source:** no second source confirmed or contradicted this.",
                consensus.CONFLICT: "⚠️ **Sources disagree:** the first says «{v}», the second «{s}». Double-check it."}}


def scan_code(code: str) -> list[str]:
    """Security issues found by reading the code's syntax tree (empty list = safe)."""
    try:
        tree = ast.parse(code)
    except SyntaxError as err:
        return [f"خطأ في الصياغة: {err.msg} (سطر {err.lineno})"]
    issues = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mods = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            issues += [f"استيراد ممنوع: {m}" for m in mods if m.split(".")[0] in BANNED_IMPORTS]
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in BANNED_CALLS:
            issues.append(f"دالة ممنوعة: {node.func.id}()")
        elif isinstance(node, ast.Attribute) and node.attr.startswith("__") and node.attr.endswith("__"):
            issues.append(f"وصول ممنوع إلى خاصية داخلية: {node.attr}")
    return list(dict.fromkeys(issues))


class CriticSecurityAgent(BaseAgent):
    name = "Critic"
    sector = "الهندسة والأمان"
    timeout = 2.0

    def review_intent(self, text: str, intent: str, confidence: float) -> tuple[str, str]:
        """The existing critic rules decide when the brain is unsure or implausible."""
        return critic.review_intent(text, intent, confidence)

    def check_command(self, command: str) -> list[str]:
        return [f"أمر خطير مرفوض: {command}"] if _BLOCKED.search(command or "") else []

    def allowed(self, plan: dict, task: Task) -> tuple[bool, str]:
        """Pre-execution gate: code/system work only on the developer's machine, and only if safe."""
        if plan["primary"] == "Sandbox" and plan["intent"] != "file" and not task.allow_exec:
            return False, ("تنفيذ الكود والأوامر متاح على جهاز المطوّر فقط." if task.lang == "ar" else
                           "This needs code/system execution, which is available only on the developer's machine.")
        code = task.context.get("code", "")
        issues = scan_code(code) if code else self.check_command(task.context.get("command", ""))
        return (False, "؛ ".join(issues)) if issues else (True, "اجتاز الفحص الأمني")

    def verify(self, result: AgentResult) -> tuple[bool, str]:
        """Post-execution check of one agent's answer."""
        if not result.ok:
            return False, "الوكيل لم يقدّم إجابة"
        if result.agent in KNOWLEDGE and not any(s.startswith("http") for s in result.sources):
            return False, "إجابة معرفية بلا مصدر يمكن التحقق منه"
        if "```" in result.answer and result.agent.startswith("Code"):
            blocks = re.findall(r"```(?:python|py)\n(.*?)```", result.answer, re.S)
            bad = [i for b in blocks for i in scan_code(b) if i.startswith("خطأ")]
            if bad:
                return False, bad[0]
        return result.confidence >= 0.5, f"الثقة {result.confidence:.0%}"

    def cross_check(self, primary: AgentResult, witnesses: list[AgentResult], lang: str) -> tuple[str, str]:
        """(status, badge) comparing a fact with independent witnesses' texts."""
        texts = " ".join(w.data.get("text", w.answer) for w in witnesses if w.ok)
        if not primary.data or not texts:
            return consensus.SINGLE, BADGE[lang][consensus.SINGLE] if primary.agent in KNOWLEDGE else ""
        status, seen = consensus.judge(primary.data, texts)
        value = re.sub(r"\*", "", str(primary.data.get("value", "")))
        return status, BADGE[lang][status].format(v=value, s=seen)

    def alternatives(self, agent: str, tried: set[str]) -> list[str]:
        return [a for a in FALLBACKS.get(agent, []) if a not in tried]

    def handle(self, task: Task) -> AgentResult:
        """Stand-alone review of a piece of code or a command found in the task."""
        code = task.context.get("code", "")
        issues = scan_code(code) if code else self.check_command(task.context.get("command", task.text))
        self.step("سَداة تفحص الطلب أمنيًا", "؛ ".join(issues) or "لا مشكلات", "warn" if issues else "ok")
        if issues:
            return AgentResult(self.name, False, "⛔ " + "؛ ".join(issues), 0.95, data={"issues": issues})
        return self.ok("✅ لا توجد مشكلات أمنية.", 0.9, data={"issues": []})
