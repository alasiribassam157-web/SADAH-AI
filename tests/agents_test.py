"""Offline checks for the agents bus and the cross-checking Critic.  Run:  py -m tests.agents_test"""
import sys
import time

from agents import consensus, knowledge, supervisor
from agents.bus import Bus
from agents.message import ANSWER, FAIL, Message

failures = []


def check(name: str, ok: bool, got=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        failures.append(f"{name}: {got!r}")


# --- numbers in text
nums = [n for n, _ in consensus.numbers("يبلغ عدد سكانها ١٢٥٫٧ مليون نسمة، ومساحتها 377,975 كم²")]
check("arabic digits + مليون", 125_700_000 in [round(n) for n in nums], nums)
check("thousands separator", 377_975 in nums, nums)
check("billion", consensus.numbers("about 1.4 billion people")[0][0] == 1.4e9)

# --- numeric facts
pop = {"kind": "quantity", "amount": "+123294513", "value": "123,294,513", "prop": "P1082"}
check("population agrees (5%)", consensus.judge(pop, "عدد سكانها حوالي 125 مليون نسمة")[0] == consensus.VERIFIED)
check("population conflicts", consensus.judge(pop, "ويبلغ عدد السكان 80 مليون نسمة")[0] == consensus.CONFLICT)
check("unrelated number is not a conflict",
      consensus.judge(pop, "تأسست عام 660 وفيها 47 محافظة")[0] == consensus.SINGLE)
# real sentences from Arabic Wikipedia (Nov 2026)
check("dots as thousands (الرياض)", consensus.judge({"kind": "quantity", "amount": "+7009100", "prop": "P1082"},
      "يسكن مدينة الرياض 7.009.120 مليون نسمة وفق إحصائيات")[0] == consensus.VERIFIED)
check("comma as decimal (الكويت)", consensus.judge({"kind": "quantity", "amount": "+4670000", "prop": "P1082"},
      "وسكانها كما في آخر إحصاء 4,67 مليون نسمة")[0] == consensus.VERIFIED)
check("area (مصر)", consensus.judge({"kind": "quantity", "amount": "+1010407.87", "prop": "P2046"},
      "مساحتها نحو 1,010,408 كيلومترا مربعا، المأهولة منها 78,990 كم2")[0] == consensus.VERIFIED)
check("no text = single", consensus.judge(pop, "")[0] == consensus.SINGLE)

# --- names and dates
cap = {"kind": "wikibase-entityid", "value": "طوكيو", "prop": "P36"}
check("capital found", consensus.judge(cap, "اليابان دولة عاصمتها وأكبر مدنها طوكيو.")[0] == consensus.VERIFIED)
check("capital with prefix و", consensus.judge(cap, "أكبر المدن هي أوساكا وطوكيو")[0] == consensus.VERIFIED)
check("capital missing", consensus.judge(cap, "اليابان دولة جزرية في شرق آسيا")[0] == consensus.SINGLE)
check("no partial-word match", consensus.judge({"kind": "string", "value": "روما"}, "رومانيا دولة")[0]
      == consensus.SINGLE)
check("ال is ignored", consensus.judge({"kind": "wikibase-entityid", "value": "الرياض"},
                                       "عاصمتها مدينة رياض")[0] == consensus.VERIFIED)
born = {"kind": "time", "value": "14 مارس 1879", "prop": "P569"}
check("year agrees", consensus.judge(born, "ألبرت أينشتاين (1879 - 1955) عالم فيزياء")[0] == consensus.VERIFIED)
check("year inside a bigger number is ignored", consensus.judge(born, "رقم 218790")[0] == consensus.SINGLE)

# --- bus: parallel, deadline, primary + grace
def slow(req):
    time.sleep(3)
    return Message("Slow", ANSWER, value="late")


def fast(req):
    return Message("Fast", ANSWER, value="ok")


bus = Bus(deadline=5)
t0 = time.time()
replies = bus.ask({"Fast": fast, "Slow": slow}, {"text": "q"}, primary="Fast", grace=0.3)
check("witness gets only the grace period", time.time() - t0 < 1.5, time.time() - t0)
check("late witness answers FAIL", replies["Slow"].kind == FAIL and replies["Fast"].kind == ANSWER)
check("transcript: request + 2 replies", len(bus.transcript) == 3 and len(bus.steps()) == 3)
check("crash becomes FAIL", Bus(1).ask({"X": lambda r: 1 / 0}, {})["X"].kind == FAIL)

# --- supervisor with fake sources (no network)
def fake_wd(value, amount=None, kind="wikibase-entityid"):
    data = {"answer": f"عاصمة اليابان هي **{value}**.", "url": "https://www.wikidata.org/wiki/Q17", "name": "اليابان",
            "value": value, "kind": kind, "amount": amount, "prop": "P36"}
    return lambda req: Message("Wikidata", ANSWER, content=data["answer"], value=value, evidence=data["url"], data=data)


def fake_wp(text):
    return lambda req: Message("Wikipedia", ANSWER, content=text, value="اليابان", evidence="https://ar.wikipedia.org/wiki/x")


orig = knowledge.wikidata, knowledge.wikipedia, knowledge.researcher
try:
    knowledge.wikidata, knowledge.wikipedia = fake_wd("طوكيو"), fake_wp("عاصمتها طوكيو")
    r = supervisor.research("ما هي عاصمة اليابان")
    check("verified badge", r.ok and "✅" in r.output and "طوكيو" in r.output, r.output)
    check("both sources linked", r.output.count("🔗 http") == 2, r.output)
    check("trace has the critic", any("Critic" in s["title"] for s in r.trace), r.trace)
    knowledge.wikipedia = fake_wp("اليابان دولة جزرية")
    r = supervisor.research("ما هي عاصمة اليابان")
    check("single-source badge", "ℹ️" in r.output and r.output.count("🔗 http") == 1, r.output)
    knowledge.wikidata = lambda req: Message("Wikidata", FAIL, content="لا توجد معلومة")
    knowledge.researcher = lambda req: Message("Researcher", ANSWER, content="نص", value="اليابان",
                                               evidence="https://ar.wikipedia.org/wiki/x", data={"title": "اليابان"})
    r = supervisor.research("ما هي عاصمة اليابان")
    check("falls back to the researcher", r.ok and r.output.startswith("**اليابان**"), r.output)
finally:
    knowledge.wikidata, knowledge.wikipedia, knowledge.researcher = orig

print(f"\n{'All agent checks passed' if not failures else f'{len(failures)} failed'}")
for f in failures:
    print("  ✗", f)
sys.exit(1 if failures else 0)
