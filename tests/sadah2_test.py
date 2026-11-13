"""Offline checks for the SADAH 2.0 micro-agents (no network).  Run:  py -m tests.sadah2_test"""
import sys
import time

from agent.base_agent import AgentResult, BaseAgent, Task
from agent.companion_agent import CompanionAgent
from agent.critic_security_agent import CriticSecurityAgent, scan_code
from agent.message_bus import MessageBus
from agent.supervisor_agent import SupervisorAgent

failures = []


def check(name: str, ok: bool, got=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        failures.append(f"{name}: {got!r}")


def fake(name: str, answer: str = "", conf: float = 0.9, sources=(), data=None, delay: float = 0.0, ok=True):
    """A stand-in agent for tests: replies with a fixed answer after `delay` seconds."""
    class Fake(BaseAgent):
        def handle(self, task):
            time.sleep(delay)
            return self.ok(answer, conf, sources, data) if ok else self.fail("لا شيء")
    Fake.name = name
    return Fake()


# --- phase 1: base agent + bus
check("task detects Arabic", Task("مرحبا").lang == "ar" and Task("hello").lang == "en")
boom = fake("Boom")
boom.handle = lambda task: 1 / 0
crashed = boom.run(Task("q"))
check("crash becomes an honest failure", not crashed.ok and "ZeroDivisionError" in crashed.answer, crashed.answer)
bus = MessageBus().register(fake("Fast", "ok", delay=0.1), fake("Slow", "late", delay=3), fake("Mid", "mid", delay=1.2))
bus.agents["Slow"].timeout = 1.0
t0 = time.time()
r = bus.broadcast(["Fast", "Slow", "Mid", "Ghost"], Task("q"))
check("each agent keeps its own deadline", time.time() - t0 < 2.0 and not r["Slow"].ok and r["Mid"].ok, time.time() - t0)
check("unknown agent fails, never blocks", not r["Ghost"].ok)
bus.reset()
t0 = time.time()
r = bus.broadcast(["Fast", "Mid"], Task("q"), primary="Fast", grace=0.3)
check("witness gets only the grace period", time.time() - t0 < 1.0 and not r["Mid"].ok, time.time() - t0)
bus.register(fake("Weak", "x", conf=0.2))
check("first_success skips weak answers", bus.first_success(["Weak", "Fast"], Task("q")).agent == "Fast")
check("transcript becomes steps", len(bus.steps()) > 4 and all("title" in s for s in bus.steps()))

# --- phase 2: companion
comp = CompanionAgent()
check("chat reply", comp.run(Task("مرحبا كيف حالك", session="t")).ok)
check("identity is SADAH (ar)", "سَداة" in comp.run(Task("اسمي بسام", session="t")).answer)
check("identity is SADAH (en)", "SADAH" in comp.run(Task("what can you do")).answer)
check("feminine self-reference", "مساعدة ذكية" in comp.run(Task("من انت")).answer)
check("a real question is not chat", not comp.run(Task("ما هي عاصمة اليابان")).ok)
check("honest no-answer", "لم أجد" in comp.compose(Task("سؤال"), []))

# --- phase 2: supervisor
sup = SupervisorAgent()
plan = sup.run(Task("ما هي عاصمة اليابان وكم عدد سكانها")).data["parts"]
check("compound question split", len(plan) == 2, plan)
routes = {"ما هي عاصمة اليابان": ("web", "Wikidata"), "كيف تعمل الطاقة الشمسية": ("web", "Synthesis"),
          "آخر أخبار السعودية": ("web", "OpenWeb"), "ما هو التعلم الآلي": ("web", "LocalKB"),
          "حل المعادلة 2x+5=17": ("python", "SymbolicMath"), "احسب 25% من 80": ("python", "NumericMath"),
          "كم سعر الذهب": ("currency", "Markets"), "100 دولار بالريال": ("currency", "Forex"),
          "كيف أعكس نص في بايثون": ("code", "CodeArchitect"), "الطقس في جدة": ("weather", "EnvPrayer")}
for q, (intent, agent) in routes.items():
    got = sup.route(q, intent)["primary"]
    check(f"route «{q}» → {agent}", got == agent, got)

# --- phase 2: critic
crit = CriticSecurityAgent()
check("safe code passes", scan_code("def f(x):\n    return x * 2") == [])
bad = scan_code("import os\nos.system('x')\neval('1')\ny.__class__")
check("os / eval / dunder are caught", len(bad) == 3, bad)
check("syntax error reported", scan_code("def f(:")[0].startswith("خطأ"))
check("sandbox closed to the public", not crit.allowed({"primary": "Sandbox"}, Task("x"))[0])
check("knowledge needs a source", not crit.verify(AgentResult("Wiki", True, "x", 0.9))[0])
wd = fake("Wikidata", "عاصمة اليابان هي **طوكيو**.", 0.9, ["https://www.wikidata.org/wiki/Q17"],
          {"kind": "wikibase-entityid", "value": "طوكيو", "prop": "P36"})
wiki = fake("Wiki", "اليابان…", 0.7, ["https://ar.wikipedia.org/wiki/x"], {"text": "عاصمتها طوكيو"})
local = fake("LocalKB", ok=False)
bus = MessageBus().register(wd, wiki, local)
task = Task("ما هي عاصمة اليابان")
best, replies = sup.execute(bus, task, sup.route(task.text, "web"))
status, badge = crit.cross_check(best, [r for n, r in replies.items() if n != best.agent], "ar")
check("primary + witness cross-checked", best.agent == "Wikidata" and status == "verified", status)
final = comp.compose(task, [best], badge, replies["Wiki"].sources)
check("final reply has badge and both links", "✅" in final and final.count("🔗") == 2, final)
best, _ = sup.execute(bus, Task("ما هو شيء"), {"text": "ما هو شيء", "intent": "web", "primary": "LocalKB",
                                                 "witnesses": [], "fallback": ["Wiki"]})
check("critic falls back to another agent", best.agent == "Wiki" and best.ok, best.agent)

print(f"\n{'All SADAH 2.0 checks passed' if not failures else f'{len(failures)} failed'}")
for f in failures:
    print("  ✗", f)
sys.exit(1 if failures else 0)
