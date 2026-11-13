"""[11] Numeric math agent: safe arithmetic (safe_math.py walks the syntax tree with a whitelist, so no
code ever runs) and number theory (gcd, lcm, primes, bases, statistics via math_numeric.py).

Each number is computed twice by different methods; SADAH says «تحققتُ» only when both agree.
"""
import ast
import math
import statistics
from fractions import Fraction

from agent import math_engine, planner, safe_math
from agent.base_agent import AgentResult, BaseAgent, Task

NUMBER_THEORY = {"gcd", "lcm", "stats", "primes", "base", "isprime"}
_OPS = {ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b, ast.Mult: lambda a, b: a * b,
        ast.Div: lambda a, b: a / b, ast.FloorDiv: lambda a, b: a // b, ast.Mod: lambda a, b: a % b}


def exact(node):
    """Second evaluator: exact fractions for + − × ÷ and small integer powers (None = can't say)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return Fraction(str(node.value))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        inner = exact(node.operand)
        return None if inner is None else (-inner if isinstance(node.op, ast.USub) else inner)
    if isinstance(node, ast.BinOp):
        left, right = exact(node.left), exact(node.right)
        if left is None or right is None:
            return None
        if isinstance(node.op, ast.Pow):
            return left ** int(right) if right.denominator == 1 and abs(right) <= 64 else None
        op = _OPS.get(type(node.op))
        return op(left, right) if op and not (right == 0 and type(node.op) in (ast.Div, ast.FloorDiv, ast.Mod)) else None
    return None


def second_opinion(op: str, args: list[str]):
    """The same answer by a different route (None when no second route exists)."""
    if op == "expr":
        value = exact(ast.parse(args[0].replace("^", "**"), mode="eval").body)
        return None if value is None else float(value)
    if op == "sum_range":
        a, b = int(args[0]), int(args[1])
        return sum(range(a, b + 1)) if b - a <= 1_000_000 else None
    if op == "factorial":
        return math.prod(range(1, int(args[0]) + 1)) if int(args[0]) <= 3000 else None
    if op == "average":
        return statistics.fmean(float(x) for x in args[0].replace(" ", "").split(",") if x)
    return None


def same(a: str, b) -> bool:
    try:
        x = float(a)
    except ValueError:
        return False
    return math.isclose(x, float(b), rel_tol=1e-9, abs_tol=1e-9)


class NumericMathAgent(BaseAgent):
    name = "NumericMath"
    sector = "المنطق والرياضيات"
    intents = frozenset({"python"})
    keywords = r"احسب|كم يساوي|ناتج|مضروب|مجموع|متوسط|calculate|compute|factorial|sum of|average|%|\d\s*[-+*/x×÷^]\s*\d"
    timeout = 4.0

    def handle(self, task: Task) -> AgentResult:
        if math_engine.detect(task.text) in NUMBER_THEORY:
            self.step("سَداة تستخدم نظرية الأعداد", math_engine.detect(task.text))
            res = math_engine.solve(task.text)
            return self.ok(res.output, 0.9, data={"op": "number_theory"}) if res.ok else self.fail(res.output)
        plan = planner.plan_python(task.text)
        safe = plan.get("safe")
        if not safe:
            return self.fail("لم أجد عملية حسابية يمكن حسابها بأمان")
        self.step("سَداة تحسب بالمقيّم الآمن (AST)", f"{safe['op']}: {', '.join(safe['args'])[:120]}")
        try:
            result = safe_math.evaluate(safe["op"], safe["args"])
        except (ValueError, ArithmeticError, SyntaxError, TypeError, KeyError) as exc:
            return self.fail(f"تعذّر الحساب: {exc}")
        try:
            check = second_opinion(safe["op"], safe["args"])
        except (ValueError, ArithmeticError, SyntaxError, TypeError):
            check = None
        agreed = check is not None and same(result, check)
        if agreed:
            self.step("تحققتُ بطريقة حساب ثانية مستقلة فتطابق الناتج", f"{check}", confidence=0.98)
        elif check is not None:
            self.step("الطريقتان لم تتطابقا", f"{result} ≠ {check}", "warn", 0.4)
            return self.fail(f"نتيجتان مختلفتان ({result} و {check})؛ لن أقدّم رقمًا غير مؤكد.")
        answer = f"**{result}**" if "\n" not in result and len(result) < 160 else f"```\n{result}\n```"
        if agreed:
            answer += "\n\n✓ تحققتُ منه بطريقتين مستقلتين." if task.lang == "ar" else "\n\n✓ Checked two independent ways."
        return self.ok(answer, 0.98 if agreed else 0.9, data={"op": safe["op"], "value": result})
