"""Offline checks for the hotfix: personal gate, works lists, strict synthesis relevance.  Run: py -m tests.hotfix_test"""
import sys

from agent import personal_gate
from agent.base_agent import Task
from agent.critic import review_intent
from agent.chat_replies import chat_reply
from agent.companion import Companion
from agent.supervisor_agent import SupervisorAgent
from agent.synthesis_agent import on_axis
from agent.works import fetch, is_works, parse, works

failures = []


def check(name: str, ok: bool, got=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        failures.append(f"{name}: {got!r}")


# --- 1. personal gate: never a search, answered from memory
for q in ("من أنا؟", "مين انا", "وش اسمي", "ما هو اسمي", "وين أسكن", "مدينتي", "كيف حالي", "تذكرين اسمي", "who am i"):
    check(f"personal: {q}", personal_gate.is_personal(q))
    check(f"critic keeps «{q}» as chat even at 96 %", review_intent(q, "chat", 0.96)[0] == "chat"
          and review_intent(q, "web", 0.4)[0] == "chat")
for q in ("من هو ابن سينا", "ما هي عاصمة فرنسا", "كيف ابني بيت"):
    check(f"not personal: {q}", not personal_gate.is_personal(q))
for q in ("من أنت", "مين أنتِ", "عرفيني بنفسك"):
    check(f"about SADAH: {q}", personal_gate.about_sadah(q) and "سَداة" in chat_reply(q, "ar"), chat_reply(q, "ar"))
talk = Companion()
first = talk.respond("s1", "من أنا؟", "ar")
check("unknown visitor is asked for the name", first and "ما هو اسمك" in first, first)
talk.respond("s1", "اسمي بسام", "ar")
talk.respond("s1", "انا من جدة", "ar")
check("name remembered", "بسام" in talk.respond("s1", "من أنا", "ar"))
check("city remembered", "جدة" in talk.respond("s1", "وين أسكن", "ar"))
check("sessions are private", "ما هو اسمك" in talk.respond("other", "مين أنا", "ar"))

# --- 2. strict relevance for open questions
check("a sentence must share a root with its axis",
      on_axis("بناء بيت", "تختلف البيوت في إنشائها حسب البيئة") and not on_axis("بناء بيت", "أصالة نصري مغنية سورية"))
sup = SupervisorAgent.__new__(SupervisorAgent)
plan = SupervisorAgent.route(sup, "كيف ابني بيت", "web")
check("«كيف ابني بيت» has no random fallback", plan["primary"] == "Synthesis" and plan["fallback"] == [], plan)

# --- 3. works lists
check("works question detected", is_works("ماهي افلام جوني ديب ؟") and parse("ماهي افلام جوني ديب")[1] == "جوني ديب")
check("not a works question", not is_works("يعني ايه book بالعربي") and not is_works("what are the best books"))
plan = SupervisorAgent.route(sup, "ماهي افلام جوني ديب", "web")
check("works go to Wikidata with no article fallback", plan["primary"] == "Wikidata" and plan["fallback"] == [], plan)


class Resp:
    def __init__(self, body):
        self.body = body

    def json(self):
        return self.body


class Http:
    def __init__(self):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get(self, url, params=None):
        q = params.get("query", "")
        self.calls.append(q or params.get("action"))
        if params.get("action") == "wbsearchentities":
            return Resp({"search": [{"id": "Q1", "label": "جوني ديب"}]})
        if "VALUES" in q:
            return Resp({"results": {"bindings": [{"i": {"value": "http://www.wikidata.org/entity/Q1"}}]}})
        rows = [("Edward Scissorhands", 1990), ("Q123", 1991), ("Blow", 2001), ("Edward Scissorhands", 1990)]
        return Resp({"results": {"bindings": [{"wLabel": {"value": t}, "y": {"value": str(y)}} for t, y in rows]}})


res = works("ماهي افلام جوني ديب", "ar", Http())
check("film list built from the items", res and res["count"] == 2 and "• Edward Scissorhands (1990)" in res["answer"]
      and "• Blow (2001)" in res["answer"] and "Q123" not in res["answer"], res)

print("\nAll hotfix checks passed" if not failures else "\nFAILED:\n" + "\n".join(failures))
sys.exit(1 if failures else 0)
"""Offline checks for the hotfix: personal gate, works lists, strict synthesis relevance.  Run: py -m tests.hotfix_test"""
import sys

from agent import personal_gate
from agent.base_agent import Task
from agent.critic import review_intent
from agent.chat_replies import chat_reply
from agent.companion import Companion
from agent.supervisor_agent import SupervisorAgent
from agent.synthesis_agent import _enough
from agent.works import fetch, is_works, parse, works

failures = []


def check(name: str, ok: bool, got=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        failures.append(f"{name}: {got!r}")


# --- 1. personal gate: never a search, answered from memory
for q in ("من أنا؟", "مين انا", "وش اسمي", "ما هو اسمي", "وين أسكن", "مدينتي", "كيف حالي", "تذكرين اسمي", "who am i"):
    check(f"personal: {q}", personal_gate.is_personal(q))
    check(f"critic keeps «{q}» as chat even at 96 %", review_intent(q, "chat", 0.96)[0] == "chat"
          and review_intent(q, "web", 0.4)[0] == "chat")
for q in ("من هو ابن سينا", "ما هي عاصمة فرنسا", "كيف ابني بيت"):
    check(f"not personal: {q}", not personal_gate.is_personal(q))
for q in ("من أنت", "مين أنتِ", "عرفيني بنفسك"):
    check(f"about SADAH: {q}", personal_gate.about_sadah(q) and "سَداة" in chat_reply(q, "ar"), chat_reply(q, "ar"))
talk = Companion()
first = talk.respond("s1", "من أنا؟", "ar")
check("unknown visitor is asked for the name", first and "ما هو اسمك" in first, first)
talk.respond("s1", "اسمي بسام", "ar")
talk.respond("s1", "انا من جدة", "ar")
check("name remembered", "بسام" in talk.respond("s1", "من أنا", "ar"))
check("city remembered", "جدة" in talk.respond("s1", "وين أسكن", "ar"))
check("sessions are private", "ما هو اسمك" in talk.respond("other", "مين أنا", "ar"))

# --- 2. strict relevance for open questions
check("one word is not enough for «ابني بيت»", _enough({"ابني", "بيت"}) == 2 and _enough({"الخلية"}) == 1 and _enough(set("abcdef")) == 4)
sup = SupervisorAgent.__new__(SupervisorAgent)
plan = SupervisorAgent.route(sup, "كيف ابني بيت", "web")
check("«كيف ابني بيت» has no random fallback", plan["primary"] == "Synthesis" and plan["fallback"] == [], plan)

# --- 3. works lists
check("works question detected", is_works("ماهي افلام جوني ديب ؟") and parse("ماهي افلام جوني ديب")[1] == "جوني ديب")
check("not a works question", not is_works("يعني ايه book بالعربي") and not is_works("what are the best books"))
plan = SupervisorAgent.route(sup, "ماهي افلام جوني ديب", "web")
check("works go to Wikidata with no article fallback", plan["primary"] == "Wikidata" and plan["fallback"] == [], plan)


class Resp:
    def __init__(self, body):
        self.body = body

    def json(self):
        return self.body


class Http:
    def __init__(self):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get(self, url, params=None):
        q = params.get("query", "")
        self.calls.append(q or params.get("action"))
        if params.get("action") == "wbsearchentities":
            return Resp({"search": [{"id": "Q1", "label": "جوني ديب"}]})
        if "VALUES" in q:
            return Resp({"results": {"bindings": [{"i": {"value": "http://www.wikidata.org/entity/Q1"}}]}})
        rows = [("Edward Scissorhands", 1990), ("Q123", 1991), ("Blow", 2001), ("Edward Scissorhands", 1990)]
        return Resp({"results": {"bindings": [{"wLabel": {"value": t}, "y": {"value": str(y)}} for t, y in rows]}})


res = works("ماهي افلام جوني ديب", "ar", Http())
check("film list built from the items", res and res["count"] == 2 and "• Edward Scissorhands (1990)" in res["answer"]
      and "• Blow (2001)" in res["answer"] and "Q123" not in res["answer"], res)

print("\nAll hotfix checks passed" if not failures else "\nFAILED:\n" + "\n".join(failures))
sys.exit(1 if failures else 0)
