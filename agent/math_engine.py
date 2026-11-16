"""Symbolic math (SADAH v5): equations, derivatives, integrals, factoring, statistics, number theory.

Every expression is checked against a whitelist of names and a size limit before sympy reads it,
so no user code can run (sympy's parser evaluates its input).
"""
import re

import sympy as sp
from sympy.parsing.sympy_parser import (convert_xor, implicit_multiplication_application, parse_expr,
                                        standard_transformations)

from agent.math_numeric import numeric
from agent.tools import ToolResult

X, Y, Z = sp.symbols("x y z")
LOCALS = {"x": X, "y": Y, "z": Z, "sin": sp.sin, "cos": sp.cos, "tan": sp.tan, "log": sp.log, "ln": sp.log,
          "exp": sp.exp, "sqrt": sp.sqrt, "pi": sp.pi, "e": sp.E, "abs": sp.Abs}
_TRANSFORMS = standard_transformations + (implicit_multiplication_application, convert_xor)
_MATH_SPAN = re.compile(r"[0-9a-zA-Z\s+\-*/^().=,]+")
_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩×÷−", "0123456789*/-")

OPS = [  # (operation, trigger words)
    ("solve", r"حل المعادل|حل المعادلة|حل\s+\S*=|اوجد قيمة|أوجد قيمة|\bsolve\b|find x"),
    ("derivative", r"مشتق|اشتقاق|اشتق|derivative|differentiate|d/dx"),
    ("integral", r"تكامل|integral|integrate|antiderivative"),
    ("primes", r"عوامل[هـ]? الأولية|عوامل اولية|العوامل الأولية|prime factor"),
    ("factor", r"\bحلل\b|تحليل|\bfactor\b|factorise|factorize"),
    ("expand", r"\bفك\b|افرد|\bexpand\b"),
    ("simplify", r"بسط|تبسيط|simplify"),
    ("gcd", r"القاسم المشترك الأكبر|ق\.?م\.?أ|\bgcd\b|greatest common"),
    ("lcm", r"المضاعف المشترك الأصغر|م\.?م\.?أ|\blcm\b|least common multiple"),
    ("stats", r"الوسيط|median|المنوال|\bmode\b|الانحراف المعياري|standard deviation|التباين|variance|إحصاء|احصاء|statistics"),
    ("base", r"ثنائي|binary|ست عشري|سداسي عشر|hexadecimal|\bhex\b|ثماني|octal"),
    ("isprime", r"عدد أولي|عدد اولي|is \d+ (?:a )?prime"),
]


def arabic_vars(text: str) -> str:
    """Arabic school notation: a lone «س»/«ص» is x/y («3س + 2»), but not the letter inside «الطقس»."""
    text = re.sub(r"(?<![؀-ۿ])س(?![؀-ۿ])", "x", text)
    return re.sub(r"(?<![؀-ۿ])ص(?![؀-ۿ])", "y", text)


def has_math(question: str) -> bool:
    """Digits or a standalone variable: the question really contains something to compute."""
    return bool(re.search(r"\d|(?<![A-Za-z])[xyz](?![A-Za-z])", arabic_vars(question.translate(_ARABIC_DIGITS))))

STRONG_OPS = ("solve", "derivative", "integral", "factor", "expand", "simplify", "primes", "gcd", "lcm", "base", "isprime")


def detect(question: str) -> str | None:
    text = question.translate(_ARABIC_DIGITS)
    return next((op for op, pattern in OPS if re.search(pattern, text, re.IGNORECASE)), None)


def _parse(text: str):
    text = arabic_vars(text).strip(" .,")
    if not text or len(text) > 100 or "__" in text:
        raise ValueError("expression too long or empty")
    for name in re.findall(r"[A-Za-z]+", text):
        if name.lower() not in LOCALS:
            raise ValueError(f"unsupported name: {name}")
    if any(int(p) > 40 for p in re.findall(r"(?:\^|\*\*)\s*(\d+)", text)):
        raise ValueError("exponent too large")
    return parse_expr(text.lower(), local_dict=LOCALS, transformations=_TRANSFORMS)


def _math_text(question: str) -> str:
    """The longest run of math characters: «حل المعادلة 2x+5=17» -> «2x+5=17»."""
    text = arabic_vars(question.translate(_ARABIC_DIGITS))
    text = re.sub(r"\b(?:solve|derivative|of|differentiate|integrate|integral|the|simplify|factor|expand|find)\b",
                  " ", text, flags=re.IGNORECASE)
    spans = [s.strip() for s in _MATH_SPAN.findall(text) if re.search(r"[\dxyz]", s)]
    return max(spans, key=len) if spans else ""


def _show(expr) -> str:
    return str(expr).replace("**", "^").replace("*", "·").replace("sqrt", "√").replace("E", "e")


def _numbers(question: str) -> list[float]:
    return [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", question.translate(_ARABIC_DIGITS))]


def solve(question: str) -> ToolResult:
    op, ar = detect(question), bool(re.search(r"[؀-ۿ]", question))
    try:
        if op in ("gcd", "lcm", "stats", "primes", "base", "isprime"):
            return ToolResult(True, numeric(op, _numbers(question), question, ar))
        bounds = re.search(r"(?:من|from)\s*(-?[\d.]+)\s*(?:الى|إلى|to)\s*(-?[\d.]+)", question.translate(_ARABIC_DIGITS))
        text = _math_text(re.sub(r"(?:من|from)\s*-?[\d.]+\s*(?:الى|إلى|to)\s*-?[\d.]+", " ", question) if bounds else question)
        if op == "solve" or (op is None and "=" in text):
            sides = [s for s in re.split(r",|\s+و\s+", text) if "=" in s]
            equations = [sp.Eq(_parse(s.split("=")[0]), _parse(s.split("=")[1])) for s in sides]
            unknowns = sorted(set().union(*(e.free_symbols for e in equations)), key=str)
            sols = sp.solve(equations, unknowns, dict=True)
            real = [s for s in sols if all(v.is_real for v in s.values())]
            if not real:
                note = ("ما لها حل حقيقي." if ar else "No real solution.") + (
                    f" ({'الحلول المركبة' if ar else 'complex'}: {'; '.join(_show(v) for s in sols for v in s.values())})" if sols else "")
                return ToolResult(True, note)
            lines = [", ".join(f"{k} = {_show(sp.nsimplify(v))}" + (f" ≈ {float(v):.4g}" if not v.is_Rational else "")
                               for k, v in s.items()) for s in real]
            # Substitute every solution back into every equation before claiming it is right.
            verified = all(sp.simplify(e.lhs.subs(s) - e.rhs.subs(s)) == 0 for s in real for e in equations)
            check = ("✓ تحققت منه بالتعويض في المعادلة." if ar else "✓ Verified by substitution.") if verified else ""
            return ToolResult(True, ("الحل:\n" if ar else "Solution:\n") + "\n".join(f"**{l}**" for l in lines) + f"\n\n{check}")
        expr = _parse(text)
        var = sorted(expr.free_symbols, key=str)[0] if expr.free_symbols else X
        if op == "derivative":
            out, label = sp.simplify(sp.diff(expr, var)), ("المشتقة" if ar else "Derivative")
        elif op == "integral" and bounds:
            out = sp.integrate(expr, (var, sp.sympify(bounds.group(1)), sp.sympify(bounds.group(2))))
            label = (f"التكامل من {bounds.group(1)} إلى {bounds.group(2)}" if ar else f"Integral from {bounds.group(1)} to {bounds.group(2)}")
        elif op == "integral":
            out, label = sp.integrate(expr, var), ("التكامل" if ar else "Integral")
        elif op == "factor":
            out, label = sp.factor(expr), ("التحليل" if ar else "Factored")
        elif op == "expand":
            out, label = sp.expand(expr), ("بعد الفك" if ar else "Expanded")
        else:
            out, label = sp.simplify(expr), ("التبسيط" if ar else "Simplified")
        tail = " + C" if op == "integral" and not bounds else ""
        approx = f"  ≈ {float(out):.6g}" if out.is_number and not out.is_Integer else ""
        return ToolResult(True, f"{label}: **{_show(out)}{tail}**{approx}")
    except (ValueError, TypeError, SyntaxError, sp.SympifyError, NotImplementedError, ZeroDivisionError) as exc:
        return ToolResult(False, (f"ما قدرت أفهم المسألة: {exc}" if ar else f"Couldn't read the problem: {exc}"))
