"""Fast end-to-end checks run before every push.  Run:  py -m tests.smoke_test"""
import sys

from core import trainer

for _brain in ("router", "coder"):
    if not trainer.checkpoint(_brain).exists():
        trainer.train(brain=_brain)

from agent.orchestrator import NexusAgent  # noqa: E402  (needs the checkpoint)
from agent.tools import SAFE_MODE, WORKSPACE  # noqa: E402

agent = NexusAgent()
failures = []


def check(name: str, message: str, intent: str, expect_in_answer: str = "", allow_exec: bool = False):
    result = agent.handle(message, allow_exec=allow_exec)
    ok = result.get("intent") == intent and expect_in_answer in result["answer"]
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        failures.append(f"{name}: intent={result.get('intent')} answer={result['answer'][:120]!r}")


check("chat (en)", "hello there", "chat", "How can I help")
check("chat (ar)", "مرحبا كيف حالك", "chat", "أساعدك")
check("thanks", "شكرا لك", "chat", "العفو")
check("not small talk", "من اخترع المصباح الكهربائي", "web", "إديسون")
check("fact (wikidata)", "ما هي عاصمة فرنسا", "web", "باريس")
# Agents cross-check: Wikidata answers, Wikipedia is the witness, the critic labels the result.
check("fact cross-checked", "ما هي عاصمة فرنسا", "web", "✅")
check("number cross-checked", "كم عدد سكان اليابان", "web", "✅")
check("percent", "what is 25% of 80", "python", "20")
check("code python", "كيف أعكس نص في بايثون", "code", "[::-1]")
check("code java", "how to reverse a string in java", "code", "StringBuilder")
check("units", "convert 5 miles to km", "units", "8.0467")
check("equation", "حل المعادلة 2x+5=17", "python", "x = 6")
check("derivative", "derivative of x^3", "python", "3·x^2")
check("not a variable", "تحليل الطقس في جدة", "weather", "°")
check("age", "كم عمري لو انولدت 12-05-1998", "datetime", "سنة")
# Conversation memory: the follow-up has no subject of its own.
_s = "smoke-session"
agent.handle("ما هي عاصمة اليابان", session=_s)
_follow = agent.handle("وكم عدد سكانها؟", session=_s)
print(f"{'PASS' if 'نسمة' in _follow['answer'] else 'FAIL'}  follow-up memory")
if "نسمة" not in _follow["answer"]:
    failures.append(f"follow-up memory: {_follow['answer'][:120]!r}")
check("file create", "create file _smoke.txt with content ok123", "file", "Created")
check("file read", "read _smoke.txt", "file", "ok123")
# Public visitors: math runs through the safe evaluator, never as code.
check("safe calc", "calculate 2 ** 10", "python", "1024")
check("safe ^ power", "what is 3^4 + 2", "python", "83")
check("safe arabic", "احسب مضروب 5", "python", "120")
check("no code for public", "run command `whoami`", "system", "developer's machine")
if not SAFE_MODE:
    check("python calc", "calculate 2 ** 10", "python", "1024", allow_exec=True)
    check("arabic math", "احسب مضروب 5", "python", "120", allow_exec=True)

(WORKSPACE / "_smoke.txt").unlink(missing_ok=True)
for leftover in WORKSPACE.glob("run_*.py"):
    leftover.unlink()

if failures:
    print("\n".join(["", "FAILED:"] + failures))
    sys.exit(1)
print("\nAll smoke tests passed.")
