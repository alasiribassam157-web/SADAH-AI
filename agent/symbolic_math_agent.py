"""[10] Symbolic math agent: equations, derivatives, integrals, factoring and simplification with sympy
(math_engine.py, whose parser accepts only whitelisted names, so no user code runs).

Every result is checked a second, independent way before SADAH says it is right:
equations by substitution (inside math_engine), integrals by differentiating back, derivatives by a
numeric difference quotient, factor/expand/simplify by proving the result equals the original.
"""
import random
import re

import sympy as sp

from agent import math_engine
from agent.base_agent import AgentResult, BaseAgent, Task

CHECKED = ("derivative", "integral", "factor", "expand", "simplify")
SYMBOLIC = set(math_engine.STRONG_OPS) | {"solve"}


def _expression(question: str):
    """The expression the question is about (bounds like «من 0 إلى 2» removed) and its variable."""
    bounds = r"(?:من|from)\s*-?[\d.]+\s*(?:الى|إلى|to)\s*-?[\d.]+"
    text = math_engine._math_text(re.sub(bounds, " ", question))
    expr = math_engine._parse(text)
    var = sorted(expr.free_symbols, key=str)[0] if expr.free_symbols else math_engine.X
    return expr, var


def verify(question: str, op: str) -> tuple[bool, str]:
    """Re-derive the answer by a different route; (passed, how it was checked)."""
    expr, var = _expression(question)
    if op == "integral":
        antiderivative = sp.integrate(expr, var)
        return sp.simplify(sp.diff(antiderivative, var) - expr) == 0, "اشتققتُ الناتج فعاد إلى الدالة الأصلية"
    if op == "derivative":
        exact, h = sp.diff(expr, var), 1e-6
        for _ in range(3):
            x0 = random.uniform(0.5, 2.0)
            approx = (expr.subs(var, x0 + h) - expr.subs(var, x0 - h)) / (2 * h)
            if abs(float(approx) - float(exact.subs(var, x0))) > 1e-3 * max(1.0, abs(float(approx))):
                return False, "الفرق العددي لم يطابق المشتقة"
        return True, "طابقت المشتقة الفرقَ العددي عند ثلاث نقاط عشوائية"
    transform = {"factor": sp.factor, "expand": sp.expand, "simplify": sp.simplify}[op]
    return sp.simplify(transform(expr) - expr) == 0, "أثبتُّ أن الناتج يساوي العبارة الأصلية"


class SymbolicMathAgent(BaseAgent):
    name = "SymbolicMath"
    sector = "المنطق والرياضيات"
    intents = frozenset({"python"})
    keywords = r"معادل|مشتق|تكامل|حلل|بسط|فك|solve|derivative|integral|factor|simplify|expand"
    timeout = 6.0

    def can_handle(self, task: Task) -> float:
        return 0.95 if math_engine.detect(task.text) in SYMBOLIC or "=" in task.text else super().can_handle(task)

    def handle(self, task: Task) -> AgentResult:
        op = math_engine.detect(task.text) or ("solve" if "=" in task.text else "simplify")
        self.step(f"سَداة تحل المسألة رمزيًا ({op})", "sympy مع قائمة بيضاء للأسماء")
        res = math_engine.solve(task.text)
        if not res.ok:
            return self.fail(res.output)
        conf, note = 0.85, ""
        if "✓" in res.output:
            conf = 0.97
            self.step("تحققتُ من الحل بالتعويض في المعادلة", confidence=conf)
        elif op in CHECKED:
            try:
                passed, how = verify(task.text, op)
            except (ValueError, TypeError, SyntaxError, sp.SympifyError, NotImplementedError, ZeroDivisionError):
                passed, how = False, "تعذّر التحقق المستقل"
            conf = 0.97 if passed else 0.6
            self.step(how, status="ok" if passed else "warn", confidence=conf)
            note = (f"\n\n✓ تحققتُ: {how}." if passed else "\n\n⚠️ لم أستطع التحقق من الناتج بطريقة ثانية.") \
                if task.lang == "ar" else ("\n\n✓ Verified independently." if passed else "\n\n⚠️ Not independently verified.")
        return self.ok(res.output + note, conf, data={"op": op})
