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

# --- phase 6: live data checks (offline: fixed rates and real answer formats) and code agents
from agent import live_skills  # noqa: E402
from agent.code_architect_agent import CodeArchitectAgent  # noqa: E402
from agent.code_synthesizer_agent import CodeSynthesizerAgent  # noqa: E402
from agent.env_prayer_agent import in_order, plausible  # noqa: E402
from agent.forex_agent import rate_check  # noqa: E402
from agent.markets_agent import consistent  # noqa: E402
from agent.sandbox_agent import SandboxAgent  # noqa: E402

live_skills._RATES["USD"] = (9e18, {"SAR": 3.7502})
check("dollar→riyal matches the official peg", rate_check("USD", "SAR")[0] is True)
live_skills._RATES["USD"] = (9e18, {"SAR": 4.2})
check("a broken peg is caught", rate_check("USD", "SAR")[0] is False)
g24 = 2650 * 3.75 / 31.1035
gold = f"**سعر الذهب الآن:** 2,650.00 دولار للأونصة\n• عيار 24: **{g24:,.2f} ريال** للجرام"
check("gram prices follow from the ounce price", consistent(gold)[0] is True)
check("a wrong karat price is caught", consistent(gold.replace(f"{g24:,.2f}", "330.00"))[0] is False)
times = "الفجر **4:55 ص** الشروق **6:15 ص** الظهر **11:50 ص** العصر **2:55 م** المغرب **5:20 م** العشاء **6:50 م**"
check("prayer times in their natural order", in_order(times) is True and in_order(times.replace("6:50 م", "4:00 م")) is False)
check("temperatures physically plausible", plausible("**30°م** · العظمى 35°") and plausible("900°") is False)
architect = CodeArchitectAgent()
r = architect.run(Task("كيف أعكس نص في بايثون", intent="code"))
check("code answer from the verified library, syntax-checked", r.ok and "[::-1]" in r.answer and r.confidence >= 0.9)
r = CodeSynthesizerAgent(architect.coder).run(Task("اكتب برنامج بايثون يقرأ ملف ثم يرتب قائمة ثم يكتب في ملف"))
check("multi-step program assembled from three blocks", r.ok and r.data["tasks"] == ["read_file", "sort_list", "write_file"]
      and "def main():" in r.answer, r.answer[:120])
sandbox = SandboxAgent()
check("no code execution for public visitors", not sandbox.run(Task("run command `whoami`", intent="system")).ok)
check("files still work inside workspace", "Created" in sandbox.run(Task("create file _t.txt with content ok", intent="file")).answer
      and "Deleted" in sandbox.run(Task("delete _t.txt", intent="file")).answer)
check("dangerous code refused even locally", not sandbox.run(Task("```python\nimport subprocess\n```", intent="python",
                                                                   allow_exec=True)).ok)

print(f"\n{'All SADAH 2.0 tool checks passed' if not failures else f'{len(failures)} failed'}")
for f in failures:
    print("  ✗", f)
sys.exit(1 if failures else 0)
