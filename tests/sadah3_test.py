"""Offline checks for PR #6: causal «why» answers, dangling pronouns, Wikidata protection.  Run: py -m tests.sadah3_test"""
import sys
import threading
import time

from agent import wd_guard
from agent.base_agent import Task
from agent.causal import BOOST, expand, is_causal, weights
from agent.companion_agent import DANGLING, CompanionAgent
from agent.memory import ConversationMemory, is_dangling
from agent.synthesis_agent import SynthesisAgent, kind_of, textrank

failures = []


def check(name: str, ok: bool, got=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        failures.append(f"{name}: {got!r}")


# --- fix 1: causal extractor
check("«ليش» is a why question", kind_of("ليش يحدث الاحتباس الحراري") == "why")
check("search is widened with reason words", all(w in expand("الاحتباس الحراري") for w in ("أسباب", "عوامل", "تفسير", "لماذا")))
for s in ("يحدث ذلك بسبب انبعاث الغازات.", "ارتفع السعر لأن الطلب زاد كثيرًا.", "ونتيجة لـ ذلك انخفض الإنتاج.",
          "يعود ذلك إلى تغير المناخ.", "قامت الدولة بالخطوة بهدف التطوير.", "مما يؤدي إلى ارتفاع الحرارة.",
          "نظرًا لـ قلة الأمطار جفت الأنهار.", "prices rose because demand grew"):
    check(f"causal link found: {s[:28]}", is_causal(s))
check("a plain description has no causal link", not is_causal("الاحتباس الحراري ظاهرة مناخية معروفة عالميًا."))
check("causal sentences weigh 2.5×", list(weights(["بسبب الغازات ارتفعت الحرارة", "ظاهرة مناخية"])) == [BOOST, 1.0] and BOOST == 2.5)
general = "الاحتباس الحراري ظاهرة مناخية يدرسها العلماء منذ عقود طويلة في العالم."
reason = "يحدث الاحتباس الحراري بسبب انبعاث الغازات الدفيئة من المصانع والسيارات."
items = [general, reason]
plain, boosted = textrank(items, ["احتباس", "حراري"]), textrank(items, ["احتباس", "حراري"], boost=weights(items))
check("boost moves the causal sentence ahead", boosted[1] > plain[1] and boosted[1] > boosted[0], (plain, boosted))


class Local:
    def passages(self, query, lang, k):
        return []


class Wiki:
    def search(self, query, lang, n):
        return ("الاحتباس الحراري", " ".join([
            "الاحتباس الحراري ظاهرة مناخية يدرسها العلماء منذ عقود طويلة في العالم.",
            "يحدث الاحتباس الحراري بسبب انبعاث الغازات الدفيئة من المصانع والسيارات.",
            "يعود ارتفاع حرارة الأرض إلى حرق الوقود الأحفوري وقطع الغابات الواسعة.",
            "وتقيس محطات الرصد الحراري درجات الحرارة في معظم دول العالم كل عام.",
            "ويزداد الاحتباس الحراري لأن الغازات الدفيئة تحبس حرارة الشمس في الغلاف الجوي."]), "https://ar.wikipedia.org/wiki/x")


res = SynthesisAgent(Local(), Wiki()).run(Task("لماذا يحدث الاحتباس الحراري؟"))
check("why answer is made of reasons", res.ok and "بسبب" in res.answer and "يعود" in res.answer, res.answer)
check("why answer leaves the general sentence out", res.ok and "يدرسها العلماء" not in res.answer, res.answer)

# --- fix 2: dangling pronouns
for q in ("وكم عدد سكانها؟", "ما هي عاصمتها؟", "كم مساحته؟", "ما هي لغتها الرسمية", "what is its capital"):
    check(f"dangling: {q}", is_dangling(q))
for q in ("ما هي عاصمة فرنسا", "كم عدد سكان مصر", "كم الساعة", "من هو مؤسس جوجل"):
    check(f"not dangling: {q}", not is_dangling(q))
bot = CompanionAgent()
check("empty memory: SADAH asks back, feminine",
      bot.dangling(Task("وكم عدد سكانها؟", session="new")) == DANGLING["ar"] and "تسأل" in DANGLING["ar"])
bot.memory.remember("old", "اليابان")
check("with a remembered subject it is answered, not asked back", bot.dangling(Task("وكم عدد سكانها؟", session="old")) == "")
check("generic follow-up uses the subject", ConversationMemory.resolve(bot.memory, "old", "كم مساحته") == "كم مساحة اليابان")


# --- fix 3: Wikidata protection
real_sleep = time.sleep


class Resp:
    def __init__(self, code, body=None):
        self.status_code, self._body = code, body or {}

    def json(self):
        return self._body


class Http:
    def __init__(self, codes):
        self.codes, self.calls, self.live, self.peak = list(codes), 0, 0, 0
        self.lock = threading.Lock()

    def get(self, url, params=None):
        with self.lock:
            self.calls += 1
            self.live += 1
            self.peak = max(self.peak, self.live)
            code = self.codes.pop(0) if self.codes else 200
        real_sleep(0.03)
        with self.lock:
            self.live -= 1
        return Resp(code, {"ok": params.get("ids", "x")})


naps = []
wd_guard.time.sleep = naps.append
http = Http([429, 429, 200])
data = wd_guard.get(http, {"action": "wbgetentities", "ids": "Q17"})
check("429 twice, then success", data == {"ok": "Q17"} and http.calls == 3, http.calls)
check("back-off waits 0.4 s then 0.8 s", naps == [0.4, 0.8], naps)
wd_guard.get(http, {"action": "wbgetentities", "ids": "Q17"})
check("repeated query comes from the cache", http.calls == 3, http.calls)
naps.clear()
dead = Http([429] * 9)
try:
    wd_guard.get(dead, {"ids": "Q1"})
    check("persistent 429 ends in an error", False)
except Exception as exc:
    check("persistent 429 ends in an error after 3 attempts", dead.calls == 3 and naps == [0.4, 0.8], (dead.calls, exc))
wd_guard.time.sleep = real_sleep
busy = Http([])
threads = [threading.Thread(target=wd_guard.get, args=(busy, {"ids": f"Q{i}"})) for i in range(8)]
[t.start() for t in threads]
[t.join() for t in threads]
check("never more than 2 requests at once", busy.calls == 8 and busy.peak <= 2, busy.peak)
small = wd_guard.TTLCache(maxsize=2, ttl=0.05)
small.put("a", 1), small.put("b", 2), small.put("c", 3)
check("LRU drops the oldest entry", small.get("a") is None and small.get("c") == 3)
time.sleep(0.07)
check("entries expire after the TTL", small.get("c") is None)

print("\nAll PR #6 checks passed" if not failures else "\nFAILED:\n" + "\n".join(failures))
sys.exit(1 if failures else 0)
