"""Offline checks for SADAH 2.0 agents, phases 5-6 (math, units, dates, live data, code).
Run:  py -m tests.sadah2_test_tools      (symbolic-math checks run only where sympy is installed)
"""
import sys

import sympy

from agent.base_agent import Task
from agent.chrono_agent import ChronoAgent
from agent.numeric_math_agent import NumericMathAgent
from agent.units_agent import UnitsAgent, round_trip

failures = []
REAL_SYMPY = isinstance(getattr(sympy, "__version__", None), str)


def check(name: str, ok: bool, got=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        failures.append(f"{name}: {got!r}")


# --- phase 5: numeric math (two independent evaluators)
num = NumericMathAgent()
for question, expected in [("what is 25% of 80", "20"), ("calculate 2 ** 10", "1024"), ("what is 3^4 + 2", "83"),
                           ("احسب مضروب 5", "120"), ("احسب 0.1 + 0.2", "0.3"), ("مجموع الاعداد من 1 الى 100", "5050"),
                           ("متوسط 2, 4, 9", "5")]:
    r = num.run(Task(question))
    check(f"«{question}» = {expected}, checked twice", r.ok and f"**{expected}**" in r.answer and r.confidence > 0.95,
          r.answer)
check("division by zero is refused", not num.run(Task("احسب 10 / 0")).ok)

# --- phase 5: units (round trip)
units_agent = UnitsAgent()
for question, expected in [("convert 5 miles to km", "8.0467"), ("حول 100 فهرنهايت الى مئوية", "37.7778"),
                           ("كم سم في 3 انش", "7.62"), ("حول 2 كيلو الى رطل", "4.4092")]:
    r = units_agent.run(Task(question))
    check(f"«{question}» → {expected}, round trip", r.ok and expected in r.answer and r.data["round_trip"], r.answer)
check("a wrong conversion fails the round trip", round_trip("convert 5 miles to km", "**5 miles = 9.5 km**") is False)

# --- phase 5: dates (recounted a second way)
chrono = ChronoAgent()
r = chrono.run(Task("كم يوم بين 1-1-2024 و 1-3-2024"))
check("gap between two dates, recounted", r.ok and "**60 يوم**" in r.answer and r.confidence > 0.95, r.answer)
r = chrono.run(Task("كم عمري لو انولدت 29-02-2000"))
check("age for a 29 February birthday, recounted", r.ok and "سنة" in r.answer and r.confidence > 0.95, r.answer)
check("event countdown answered", chrono.run(Task("كم باقي على اليوم الوطني")).ok)

# --- phase 5: symbolic math (needs the real sympy: Vercel, Kaggle, the laptop)
if REAL_SYMPY:
    from agent.symbolic_math_agent import SymbolicMathAgent, verify
    sym = SymbolicMathAgent()
    r = sym.run(Task("حل المعادلة 2x+5=17"))
    check("equation solved and substituted back", r.ok and "x = 6" in r.answer and r.confidence > 0.95, r.answer)
    r = sym.run(Task("derivative of x^3"))
    check("derivative checked numerically", r.ok and "3·x^2" in r.answer and r.confidence > 0.95, r.answer)
    r = sym.run(Task("integral of 2x"))
    check("integral checked by differentiating back", r.ok and r.confidence > 0.95, r.answer)
    check("factor proven equal to the original", verify("factor x^2-1", "factor")[0])
else:
    print("SKIP  symbolic math (sympy is not installed here)")

print(f"\n{'All SADAH 2.0 tool checks passed' if not failures else f'{len(failures)} failed'}")
for f in failures:
    print("  ✗", f)
sys.exit(1 if failures else 0)
