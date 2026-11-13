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

# --- phase 3: knowledge agents (the library works offline; Wikipedia is replaced by a real intro)
import agent.wiki_agent as wiki_mod  # noqa: E402
from agent.local_kb_agent import LocalKBAgent  # noqa: E402
from agent.wiki_agent import WikiAgent  # noqa: E402
from agent.wikidata_agent import WikidataAgent  # noqa: E402

kb_agent = LocalKBAgent()
hit = kb_agent.run(Task("ما هو التعلم الآلي"))
check("library answers offline with a source", hit.ok and "تعلم الآلة" in hit.answer and hit.sources, hit.answer[:60])
check("library admits a missing topic", not kb_agent.run(Task("كيف أطبخ الكبسة")).ok)
check("library ranks paragraphs for synthesis", len(kb_agent.passages("الذكاء الاصطناعي في الطب", "ar", 3)) == 3)
check("wikidata only takes fact questions", WikidataAgent().can_handle(Task("ما هو الذهب")) == 0.0)
FRANCE = "فرنسا جمهورية في أوروبا الغربية. يبلغ عدد سكانها 68.6 مليون نسمة، وعاصمتها وأكبر مدنها هي باريس."
wiki_mod.intro = lambda topic, lang, timeout=5: ("فرنسا", FRANCE, "https://ar.wikipedia.org/wiki/x")
witness = WikiAgent().run(Task("ما هي عاصمة فرنسا"))
check("wikipedia witness reads the whole intro", witness.ok and witness.data["text"] == FRANCE, witness.answer)
check("witness answer quotes the capital sentence", "باريس" in witness.answer and "أوروبا" not in witness.answer)

# --- phase 4: open web, synthesis, stylist, translation (offline: library + parsing only)
from agent.open_web_agent import parse_rss, rank  # noqa: E402
from agent.stylist_agent import dedupe, polish  # noqa: E402
from agent.synthesis_agent import SynthesisAgent, axes, kind_of  # noqa: E402
from agent.translation_agent import TranslationAgent, term  # noqa: E402

RSS = ("<rss><channel><item><title>إطلاق مشروع للطاقة الشمسية في السعودية</title><link>https://x/a</link>"
       "<pubDate>Fri, 13 Nov 2026 08:00:00 GMT</pubDate><source>واس</source></item>"
       "<item><title>نتائج الدوري الإسباني</title><link>https://x/b</link></item></channel></rss>")
news = rank(parse_rss(RSS), "آخر أخبار الطاقة الشمسية")
check("RSS parsed and ranked by the question", len(news) == 1 and news[0]["source"] == "واس", news)
check("comparison split into two axes", [q for _, q in axes("قارن بين الذكاء الاصطناعي وتعلم الآلة", "compare")[1]]
      == ["الذكاء الاصطناعي", "تعلم الآلة"])
check("analysis topic cleaned", axes("حلل أهمية الذكاء الاصطناعي", kind_of("حلل أهمية الذكاء الاصطناعي"))[0]
      == "الذكاء الاصطناعي")
open_answer = SynthesisAgent().run(Task("كيف يعمل التعلم المعزز"))
check("synthesis answers an open question from sources", open_answer.ok and open_answer.sources
      and "•" in open_answer.answer and "التعلم المعزز" in open_answer.answer, open_answer.answer[:120])
SUN = "الطاقة الشمسية مصدر متجدد للكهرباء"
check("stylist removes repeats and citation marks", dedupe([polish(SUN + " (Solar energy)[1]"), polish(SUN)])
      == [SUN + "."], dedupe([polish(SUN + " (Solar energy)[1]"), polish(SUN)]))
check("dictionary translation", "cat" in TranslationAgent().run(Task("ترجم قطة للانجليزي")).answer)
check("offline term lookup", term("قطة") == "cat" and term("water") == "ماء")

print(f"\n{'All SADAH 2.0 checks passed' if not failures else f'{len(failures)} failed'}")
for f in failures:
    print("  ✗", f)
sys.exit(1 if failures else 0)
