"""Live certification: POSTs to the public /api/chat and checks the 7 critical conversations plus one case per sector.

Run:  python tests/launch_certification.py [https://sadah-app.vercel.app]
The conversation runs in one session and carries the `context` back and forth, exactly like the browser does.
"""
import json
import sys
import urllib.request

URL = (sys.argv[1] if len(sys.argv) > 1 else "https://sadah-app.vercel.app").rstrip("/") + "/api/chat"
BAD = ["عبد السلام ياسين", "حاتم علي", "أنا وأخواتي", "الكابتن ماجد", "Bitbucket", "بيت التمويل", "Django"]
# (message, words of which at least one must appear, intent or None)
CRITICAL = [
    ("من انا؟", ["اسمك"], "chat"), ("بسام", ["بسام", "تشرفت"], "chat"),
    ("لقد اقول لك انا بسام", ["بسام"], "chat"), ("لا يعمي انا بسام", ["بسام"], "chat"),
    ("هل فهمت ما اقصده ؟", ["قصدك", "وضّح", "أسمعك"], "chat"),
    ("كيف ابني بيت ؟", ["لم أجد", "بناء", "منزل"], None),
    ("ماهي افلام جوني ديب ؟", ["Edward Scissorhands", "إدوارد ذو الأيدي المقصات", "Pirates", "قراصنة"], None),
]
SECTORS = [   # one case per agent family: chat, Wikidata + Wiki, math, units, forex, weather, time, code, translate, files
    ("مرحبا", ["أهلاً"]), ("ما هي عاصمة فرنسا؟", ["باريس"]), ("من هو ابن سينا", ["ابن سينا"]),
    ("كم يساوي 15 ضرب 7", ["105"]), ("حول 10 كيلومتر الى ميل", ["6.2137"]), ("حول 100 دولار الى ريال", ["ريال"]),
    ("الطقس في الرياض", ["°"]), ("كم الساعة", ["🕐"]), ("كيف أعكس نص في بايثون", ["[::-1]"]),
    ("ترجم hello للعربي", ["مرحبا"]), ("من أنت", ["سَداة"]), ("ما هو الذكاء الاصطناعي", ["ذكاء"]),
]


def ask(message, session, context):
    body = json.dumps({"message": message, "session": session, "context": context}).encode()
    req = urllib.request.Request(URL, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def main() -> int:
    failed, ctx = 0, {}
    for i, (msg, words, intent) in enumerate(CRITICAL, 1):
        res = ask(msg, "cert-session", ctx)
        ctx = res.get("context", ctx)
        ok = any(w in res["answer"] for w in words) and not any(b in res["answer"] for b in BAD) \
            and (intent is None or res["intent"] == intent)
        failed += not ok
        print(("PASS" if ok else "FAIL"), f"[{i}] {msg} -> [{res['intent']}] {res['answer'][:90]!r}")
    for n, (msg, words) in enumerate(SECTORS, 1):
        res = ask(msg, f"cert-{n}", {})
        ok = any(w in res["answer"] for w in words)
        failed += not ok
        print(("PASS" if ok else "FAIL"), f"[sector {n}] {msg} -> [{res['intent']}] {res['answer'][:70]!r}")
    print("ALL PASSED" if not failed else f"{failed} FAILED")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
