"""Offline checks for the fact shield: core facts with no network, the silent text fallback, the Wikidata breaker.
Run:  py -m tests.shield_test
"""
import sys
import time

import httpx

from agent import core_facts, fact_fallback, wd_guard
from agent.base_agent import Task
from agent.fact_resolver import resolve
from agent.wikidata_agent import WikidataAgent

failures = []


def check(name: str, ok: bool, got=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        failures.append(f"{name}: {got!r}")


# --- the 24-question load, answered locally even when the network is dead
QS = [("ما هي عاصمة فرنسا", "باريس"), ("ما هي عاصمة اليابان", "طوكيو"), ("ما هي عاصمة مصر", "القاهرة"),
      ("كم عدد سكان مصر", "112,700,000"), ("كم عدد سكان الكويت", "4,310,000"), ("عملة تركيا", "ليرة تركية"),
      ("عملة اليابان", "ين ياباني"), ("ما هي عاصمة ألمانيا", "برلين"), ("ما هي عاصمة كندا", "أوتاوا"),
      ("كم مساحة السعودية", "2,149,690"), ("كم مساحة مصر", "1,010,408"), ("متى تأسست السعودية", "1932")]
agent = WikidataAgent()
t0 = time.perf_counter()
results = [(q, agent.run(Task(q)), want) for q, want in QS + QS]
ms = (time.perf_counter() - t0) * 1000
for q, r, want in results[:12]:
    check(f"«{q}» ← {want}", r.ok and want in r.answer and r.sources[0].startswith("http"), r.answer)
check("24/24 answered", sum(r.ok for _, r, _ in results) == 24)
check(f"24 answers without network in {ms:.0f} ms (< 500)", ms < 500, ms)
check("Wikidata answer keeps its raw value for the cross-check", results[3][1].data["kind"] == "quantity"
      and results[3][1].data["amount"] == 112700000)
check("spelling variants match", core_facts.known("الامارات العربية المتحدة") and core_facts.known("USA")
      and core_facts.known("مصر") and not core_facts.known("أتلانتس"))
check("English works too", "Tokyo" in resolve("capital of Japan", "en")["answer"])
check("people and companies", "Ulm" in resolve("where was Einstein born", "en")["answer"]
      and "Jobs" in resolve("who founded apple", "en")["answer"])

# --- silent fallback: unknown to the shield, Wikidata dead (offline stub) → Wikipedia text
PAGES = {"ar": ("كوستاريكا", "كوستاريكا دولة في أمريكا الوسطى. عاصمتها سان خوسيه وعملتها الرسمية الكولون. "
                "تبلغ مساحتها 51,100 كم² ويبلغ عدد سكانها 5,200,000 نسمة. تأسست عام 1821.", "https://ar.wikipedia.org/wiki/x")}
import agent.research as research  # noqa: E402

research.intro = lambda topic, lang, timeout=5: PAGES["ar"] if "كوستا" in topic else None
for q, want in [("ما هي عاصمة كوستاريكا", "سان خوسيه"), ("كم مساحة كوستاريكا", "51,100"),
                ("كم عدد سكان كوستاريكا", "5,200,000"), ("متى تأسست كوستاريكا", "1821")]:
    r = agent.run(Task(q))
    check(f"fallback «{q}»", r.ok and want in r.answer and r.data.get("source") == "fallback", r.answer)
check("nothing anywhere → honest failure, no crash", not agent.run(Task("ما هي عاصمة أتلانتس")).ok)
check("extract: English capital", fact_fallback.extract("P36", "Its capital is Paris, and the largest city.", "en")[0] == "Paris")
check("extract: continent", fact_fallback.extract("P30", "دولة تقع في قارة آسيا", "ar")[0] == "آسيا")
check("extract: ignores an unrelated number", fact_fallback.extract("P1082", "تأسست عام 1950", "ar") is None)

# --- breaker: after the retries fail, Wikidata is skipped at once for a while
wd_guard.DELAYS = (0, 0)


class Dead:
    calls = 0

    def get(self, *a, **k):
        Dead.calls += 1
        raise httpx.TimeoutException("slow")


for _ in range(2):
    try:
        wd_guard.get(Dead(), {"x": str(time.time())})
    except httpx.HTTPError:
        pass
check("breaker opens: 2nd call makes no request", Dead.calls == 3, Dead.calls)

print(f"\n{'All shield checks passed' if not failures else f'{len(failures)} failed'}")
for f in failures:
    print("  ✗", f)
sys.exit(1 if failures else 0)
